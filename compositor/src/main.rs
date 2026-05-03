mod state;

use std::{os::fd::AsFd, sync::Arc, time::Duration};

use smithay::{
    backend::{
        input::{Event, InputEvent, KeyboardKeyEvent},
        renderer::{
            damage::OutputDamageTracker,
            element::{
                surface::{render_elements_from_surface_tree, WaylandSurfaceRenderElement},
                Kind,
            },
            gles::GlesRenderer,
        },
        winit::{self, WinitEvent},
    },
    input::keyboard::FilterResult,
    output::{Mode as OutputMode, Output, PhysicalProperties, Scale, Subpixel},
    reexports::{
        calloop::{generic::Generic, EventLoop, Interest, Mode, PostAction},
        wayland_server::{Display, ListeningSocket},
    },
    utils::{Point, Transform, SERIAL_COUNTER},
};
use state::{CalloopData, ClientState, SpaiState};
use tracing::info;

fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    info!("spai-compositor starting");

    let (mut backend, winit_evt_loop) =
        winit::init::<GlesRenderer>().map_err(|e| anyhow::anyhow!("{e}"))?;
    info!("Winit window {}×{}", backend.window_size().w, backend.window_size().h);

    let mut event_loop: EventLoop<'_, CalloopData> = EventLoop::try_new()?;
    let display: Display<SpaiState> = Display::new()?;
    let display_fd = display.as_fd().try_clone_to_owned()?;
    let state = SpaiState::new(&display.handle());
    let mut data = CalloopData { state, display };

    // Output sized to the winit window
    let win_size = backend.window_size();
    let mode = OutputMode { size: win_size, refresh: 60_000 };
    let output = Output::new(
        "winit-1".into(),
        PhysicalProperties {
            size: (0, 0).into(),
            subpixel: Subpixel::Unknown,
            make: "spai".into(),
            model: "winit".into(),
        },
    );
    output.set_preferred(mode);
    // Flipped180 compensates for OpenGL's Y=0-at-bottom vs Wayland's Y=0-at-top
    output.change_current_state(
        Some(mode),
        Some(Transform::Flipped180),
        Some(Scale::Integer(1)),
        Some(Point::from((0, 0))),
    );
    output.create_global::<SpaiState>(&data.display.handle());
    info!("Output registered: {}×{}", win_size.w, win_size.h);

    let mut damage_tracker = OutputDamageTracker::from_output(&output);

    // ── WinitEventLoop registered as a calloop source (proper fd-based polling)
    event_loop
        .handle()
        .insert_source(winit_evt_loop, |event, _, data: &mut CalloopData| {
            match event {
                WinitEvent::Focus(focused) => {
                    info!("winit focus: {}", focused);
                    if focused {
                        let surface = data
                            .state
                            .toplevels
                            .last()
                            .filter(|t| t.alive())
                            .map(|t| t.wl_surface().clone());
                        if let Some(s) = surface {
                            if let Some(kb) = data.state.seat.get_keyboard() {
                                kb.set_focus(
                                    &mut data.state,
                                    Some(s),
                                    SERIAL_COUNTER.next_serial(),
                                );
                                info!("keyboard focus set on focus_gained");
                            }
                        }
                    } else if let Some(kb) = data.state.seat.get_keyboard() {
                        kb.set_focus(&mut data.state, None, SERIAL_COUNTER.next_serial());
                    }
                }
                WinitEvent::Input(InputEvent::Keyboard { event }) => {
                    info!("key: {:?} {:?}", event.key_code(), event.state());
                    if let Some(kb) = data.state.seat.get_keyboard() {
                        kb.input::<(), _>(
                            &mut data.state,
                            event.key_code(),
                            event.state(),
                            SERIAL_COUNTER.next_serial(),
                            event.time_msec(),
                            |_, _, _| FilterResult::Forward,
                        );
                    }
                    data.display.flush_clients().ok();
                }
                WinitEvent::CloseRequested => info!("Window close requested"),
                _ => {}
            }
        })
        .expect("failed to insert winit event source");

    // ── Listening socket ──────────────────────────────────────────────────────
    let listening_socket = ListeningSocket::bind("wayland-spai")
        .unwrap_or_else(|_| ListeningSocket::bind_auto("wayland", 1..).expect("no socket"));
    let socket_name = listening_socket
        .socket_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_else(|| "wayland-spai".into());
    info!("WAYLAND_DISPLAY={}", socket_name);

    event_loop.handle().insert_source(
        Generic::new(listening_socket, Interest::READ, Mode::Level),
        |_, socket, data| {
            while let Some(stream) = socket.accept()? {
                data.display
                    .handle()
                    .insert_client(stream, Arc::new(ClientState::default()))
                    .expect("insert_client failed");
            }
            Ok(PostAction::Continue)
        },
    )?;

    event_loop.handle().insert_source(
        Generic::new(display_fd, Interest::READ, Mode::Level),
        |_, _, data| {
            data.display.dispatch_clients(&mut data.state)?;
            Ok(PostAction::Continue)
        },
    )?;

    info!("Ready. Run: WAYLAND_DISPLAY={} weston-terminal", socket_name);

    // ── Main loop: render at ~60fps ───────────────────────────────────────────
    event_loop.run(Some(Duration::from_millis(16)), &mut data, |data| {
        data.display.flush_clients().ok();

        if let Ok((renderer, mut fb)) = backend.bind() {
            let mut render_elements: Vec<WaylandSurfaceRenderElement<GlesRenderer>> = Vec::new();
            for toplevel in data.state.toplevels.iter().filter(|t| t.alive()) {
                let elems = render_elements_from_surface_tree(
                    renderer,
                    toplevel.wl_surface(),
                    (0, 0),
                    1.0,
                    1.0,
                    Kind::Unspecified,
                );
                render_elements.extend(elems);
            }
            damage_tracker
                .render_output(
                    renderer,
                    &mut fb,
                    0,
                    &render_elements,
                    [0.05, 0.05, 0.10, 1.0],
                )
                .ok();
        }
        backend.submit(None).ok();
    })?;

    Ok(())
}
