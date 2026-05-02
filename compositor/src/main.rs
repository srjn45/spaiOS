mod state;

use std::{os::fd::AsFd, sync::Arc};

use smithay::{
    backend::{
        renderer::{gles::GlesRenderer, Color32F, Frame, Renderer},
        winit::{self, WinitEvent},
    },
    output::{Mode as OutputMode, Output, PhysicalProperties, Scale, Subpixel},
    reexports::{
        calloop::{generic::Generic, EventLoop, Interest, Mode, PostAction},
        wayland_server::{Display, ListeningSocket},
    },
    utils::{Point, Rectangle, Transform},
};
use state::{CalloopData, ClientState, SpaiState};
use tracing::info;

fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    info!("spai-compositor starting");

    let (mut backend, mut winit_evt_loop) =
        winit::init::<GlesRenderer>().map_err(|e| anyhow::anyhow!("{e}"))? ;
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
    output.change_current_state(
        Some(mode),
        Some(Transform::Normal),
        Some(Scale::Integer(1)),
        Some(Point::from((0, 0))),
    );
    output.create_global::<SpaiState>(&data.display.handle());
    info!("Output registered: {}×{}", win_size.w, win_size.h);

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

    event_loop.run(
        Some(std::time::Duration::from_millis(16)),
        &mut data,
        |data| {
            data.display.flush_clients().ok();

            winit_evt_loop.dispatch_new_events(|event| {
                if let WinitEvent::CloseRequested = event {
                    info!("Window close requested");
                }
            });

            // Render a frame: dark background (client surfaces added later)
            let size = backend.window_size();
            {
                if let Ok((renderer, mut fb)) = backend.bind() {
                    if let Ok(mut frame) = renderer.render(&mut fb, size, Transform::Normal) {
                        let full = Rectangle::new((0, 0).into(), size);
                        frame.clear(Color32F::from([0.05, 0.05, 0.10, 1.0]), &[full]).ok();
                        frame.finish().ok();
                    }
                }
            }
            backend.submit(None).ok();
        },
    )?;

    Ok(())
}
