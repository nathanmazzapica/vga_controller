import argparse

VRAM_SIZE = 80 * 60

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("text", help="Text to display")
    parser.add_argument("-o", "--output", default="vram.mem")
    args = parser.parse_args()

    data = args.text.encode("ascii")

    if len(data) > VRAM_SIZE:
        parser.error(f"Text exceeds VRAM capacity ({VRAM_SIZE} bytes)")

    with open(args.output, "w") as f:
        for byte in data:
            f.write(f"{byte:02X}\n")

        for _ in range(VRAM_SIZE - len(data)):
            f.write("00\n")

    print(f"Wrote {VRAM_SIZE} bytes to {args.output}")

if __name__ == "__main__":
    main()
