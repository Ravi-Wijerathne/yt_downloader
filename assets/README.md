# Assets Directory

Place your application assets here.

## Required Files

- `icon.png` - Application icon (256x256 recommended)

## Creating an Icon

You can use any image editor to create a PNG icon with these specifications:
- Size: 256x256 pixels
- Format: PNG with transparency
- Design: YouTube-related theme (play button, download arrow, etc.)

For Windows .exe building, you may also need an `.ico` file.
Convert PNG to ICO using online tools or ImageMagick:

```bash
magick icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```
