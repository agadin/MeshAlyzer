#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET
import cairosvg

# Directories for input SVGs and output PNGs
INPUT_DIR = "./img"
OUTPUT_DIR = "./img/white"


def process_svg_file(input_path, output_path):
    try:
        # Parse the SVG file
        tree = ET.parse(input_path)
        root = tree.getroot()

        # Update fill attributes and inline style fills to white
        for elem in root.iter():
            if 'fill' in elem.attrib:
                elem.attrib['fill'] = "#ffffff"
            if 'stroke' in elem.attrib:
                elem.attrib['stroke'] = "#ffffff"
            if 'style' in elem.attrib:
                # Split the style attribute into individual properties
                style_parts = elem.attrib['style'].split(';')
                new_parts = []
                for part in style_parts:
                    if part.strip().startswith("fill:"):
                        new_parts.append("fill:#ffffff")
                    elif part.strip().startswith("stroke:"):
                        new_parts.append("stroke:#ffffff")
                    else:
                        new_parts.append(part)
                elem.attrib['style'] = ';'.join(new_parts)

        # Convert modified SVG tree back to bytes
        svg_data = ET.tostring(root, encoding="utf-8")

        # Convert the SVG (with white fills) to PNG using cairosvg
        cairosvg.svg2png(bytestring=svg_data, write_to=output_path)
        print(f"Saved white PNG: {output_path}")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")


def main():
    # Create the output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Loop over all files in the input directory
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".svg"):
            input_path = os.path.join(INPUT_DIR, filename)
            # Create the output file name with .png extension
            output_filename = os.path.splitext(filename)[0] + ".png"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            print(f"Processing {input_path}...")
            process_svg_file(input_path, output_path)


if __name__ == "__main__":
    main()
