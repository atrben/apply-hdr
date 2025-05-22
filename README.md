# HDR Emoji Maker

A tool to create Slack-friendly emojis with HDR effects.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install ImageMagick:
   ```bash
   brew install imagemagick
   ```

3. Run the application:
   ```bash
   python app.py
   ```

## Usage

- Upload an image.
- Use the canvas to draw highlights on areas you want to apply HDR effects.
- Check 'Highlight Entire Image' if you want to apply HDR to the whole image.
- Click 'Process' to apply HDR effects and resize the image to 128x128 for Slack.
- Click 'Download' to save the processed image. 