# Streaming and encoding

Views are rendered server side and streamed to the browser through
[trame-rca](https://github.com/Kitware/trame-rca/). Each view owns a scheduler
which captures its render window, encodes the frames and pushes them to the
client.

## Encoding modes

The encoder is selected when registering the RCA factories, through the
`rca_encoder` parameter of `register_rca_factories` or `RemoteViewFactory`:

| `rca_encoder`                          | Transport | Requires                                  | Notes                                             |
| -------------------------------------- | --------- | ----------------------------------------- | ------------------------------------------------- |
| `None` / `"turbo-jpeg"`                | image     | turbo-jpeg (Pillow fallback)              | Default, lowest latency                           |
| `"jpeg"`, `"png"`, `"webp"`, `"avif"`  | image     | Pillow (`avif` also `pillow-avif-plugin`) | PNG is lossless, AVIF is smallest but CPU heavier |
| `"video"` (any non-image encoder name) | video     | `trame-slicer[vtkstreaming]`              | H.264/H.265/VP9/AV1 negotiated with the browser   |

Image encoders send one encoded image per frame and display them as an image
stream. The video encoder sends encoded video packets that the browser decodes
through its video decoder.

## Video dependency

Video encoding relies on the optional `vtkstreaming` extra:

```bash
pip install "trame-slicer[vtkstreaming]"
```

When it is missing, any encoder value that is not a supported image encoder
falls back to TurboJPEG and a warning is logged once. Whether video encoding is
available can be queried before building UI options:

```python
from trame_slicer.rca_view import RemoteViewFactory

if RemoteViewFactory.is_vtk_streaming_available():
    ...  # expose the video encoder option
```

## Tuning

The following parameters are forwarded to the RCA factories:

- `target_fps`: rendering rate when the view is focused.
- `blur_fps`: rendering rate when the view is not hovered.
- `interactive_quality`: image encoding quality for image encoders (video
  encoding uses its own bitrate / rate control).
- `rca_event_throttle_s`: minimum delay between two processed client input
  events.

```python
register_rca_factories(
    slicer_app.view_manager,
    server,
    rca_encoder="video",
    target_fps=30,
    blur_fps=10,
)
```

## Client requirements

Rendering happens entirely on the server, so the client only needs a modern web
browser and a network connection to the trame server: no GPU, plugin, local
Python environment or data copy is required. This keeps the client light enough
for laptops, tablets, phones and embedded displays, and keeps the data on the
server.

- Image encoding only requires the browser to display the encoded image format
  (JPEG, PNG, WebP or AVIF). Browser support for AVIF and WebP depends on the
  browser version, JPEG is supported everywhere and is the current default.
- Video encoding requires browser support for the codec negotiated with the
  server (H.264, H.265, VP9 or AV1). H.265 support in particular depends on the
  browser and its platform. Video encoding requires HTTPS connection for
  decoding on most clients including mobile devices.
- Bandwidth: image streams scale with resolution, frame rate and quality, while
  video streams use a low-latency constant bitrate, which is usually preferable
  over high-latency or low-bandwidth networks.
