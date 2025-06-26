# convert_cookies.py
# Converts a cookies.txt file into a single-line Render-compatible format

def convert_to_render_format(input_path="auth/cookies.txt", output_path="cookies_render.txt"):
    try:
        with open(input_path, "r") as f:
            lines = f.readlines()

        # Clean and format the cookie lines
        one_line = ''.join(
            line.replace('\t', '\\t').strip() + '\\n'
            for line in lines
            if not line.startswith('#') and line.strip()
        )

        with open(output_path, "w") as f:
            f.write(one_line)

        print("✅ Success! Render-compatible cookie string saved to:", output_path)
        print("📋 Copy the content from that file and paste it into Render → Environment → YT_COOKIES")

    except FileNotFoundError:
        print("❌ Error: 'cookies.txt' not found. Make sure the file exists in the same folder.")
    except Exception as e:
        print("❌ Unexpected error:", str(e))


if __name__ == "__main__":
    convert_to_render_format()