mod state;

use std::{os::fd::AsFd, sync::Arc};

use smithay::reexports::{
    calloop::{generic::Generic, EventLoop, Interest, Mode, PostAction},
    wayland_server::{Display, ListeningSocket},
};
use state::{CalloopData, ClientState, SpaiState};
use tracing::info;

fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    info!("spai-compositor starting");

    let mut event_loop: EventLoop<'_, CalloopData> = EventLoop::try_new()?;
    let display: Display<SpaiState> = Display::new()?;

    let display_fd = display.as_fd().try_clone_to_owned()?;
    let state = SpaiState::new(&display.handle());
    let mut data = CalloopData { state, display };

    let listening_socket = ListeningSocket::bind("wayland-spai")
        .unwrap_or_else(|_| ListeningSocket::bind_auto("wayland", 1..).expect("no socket"));
    let socket_name = listening_socket
        .socket_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_else(|| "wayland-spai".into());
    info!("Wayland socket: WAYLAND_DISPLAY={}", socket_name);

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
        },
    )?;

    Ok(())
}
