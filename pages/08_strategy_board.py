import streamlit as st
import streamlit.components.v1 as components

st.markdown(
    """
    <style>
        html, body {
            overflow: hidden !important;
            height: 100% !important;
        }
        [data-testid="stAppViewContainer"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stAppViewBlock"] {
            overflow: hidden !important;
            height: 100vh !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


components.html(
		"""
		<div id="strategy-board-shell" style="width:100%; height:100%; background:#0f172a;">
			<div id="strategy-board-controls" style="display:flex; gap:0.5rem; justify-content:flex-end; padding:0.5rem; background:#111827;">
				<button id="enter-fullscreen" style="padding:0.45rem 0.8rem; border:0; border-radius:0.5rem; background:#2563eb; color:white; cursor:pointer;">Fullscreen</button>
				<button id="exit-fullscreen" style="padding:0.45rem 0.8rem; border:0; border-radius:0.5rem; background:#374151; color:white; cursor:pointer;">Exit</button>
			</div>
			<iframe id="strategy-board" src="https://strategyboard.app" allowfullscreen webkitallowfullscreen style="width:100%; border:0; display:block;"></iframe>
		</div>
		<script>
			const iframe = document.getElementById('strategy-board');
			const shell = document.getElementById('strategy-board-shell');
			const controls = document.getElementById('strategy-board-controls');
			const enterFullscreenButton = document.getElementById('enter-fullscreen');
			const exitFullscreenButton = document.getElementById('exit-fullscreen');

			function resizeFrame() {
				const viewportHeight = window.innerHeight || (window.screen && window.screen.height ? window.screen.height : 900);
				const controlsHeight = 64;
				const isFullscreen = Boolean(document.fullscreenElement);
				const height = isFullscreen
					? Math.max(0, viewportHeight - controlsHeight)
					: Math.max(480, Math.min(720, Math.round(viewportHeight * 0.72) - controlsHeight));
				controls.style.display = isFullscreen ? 'flex' : 'flex';
				iframe.style.height = height + 'px';
				shell.style.height = isFullscreen ? viewportHeight + 'px' : (height + controlsHeight) + 'px';
				if (window.Streamlit && Streamlit.setFrameHeight) {
					Streamlit.setFrameHeight((isFullscreen ? viewportHeight : height + controlsHeight) + 20);
				}
			}

			async function enterFullscreen() {
				try {
					if (shell.requestFullscreen) {
						await shell.requestFullscreen();
					} else if (iframe.requestFullscreen) {
						await iframe.requestFullscreen();
					}
				} catch (error) {
					console.error('Fullscreen failed', error);
				}
			}

			async function exitFullscreen() {
				try {
					if (document.fullscreenElement && document.exitFullscreen) {
						await document.exitFullscreen();
					}
				} catch (error) {
					console.error('Exit fullscreen failed', error);
				}
			}

			enterFullscreenButton.addEventListener('click', enterFullscreen);
			exitFullscreenButton.addEventListener('click', exitFullscreen);

			window.addEventListener('resize', resizeFrame);
			document.addEventListener('fullscreenchange', resizeFrame);
			resizeFrame();
		</script>
		""",
		height=700,
		scrolling=False,
)