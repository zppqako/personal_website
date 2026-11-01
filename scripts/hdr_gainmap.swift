// Writes HDR web versions of a photo: JPEGs whose primary image is the normal (SDR)
// picture plus a gain map, so HDR screens show the HDR version and everything else
// shows the normal one.
//
// Usage: hdr_gainmap <source> <output-prefix> <quality 0-1> <long edge>...
//   writes <output-prefix>-<long edge>-hdr.jpg for every long edge.
// Called by process_photos.py; compiled into .venv/bin/hdr_gainmap on first use.

import CoreImage
import Foundation

func fail(_ message: String) -> Never {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 5, let quality = Double(args[3]) else {
    fail("usage: hdr_gainmap <source> <output-prefix> <quality> <long edge>...")
}
let source = URL(fileURLWithPath: args[1])
let prefix = args[2]
let edges = args[4...].compactMap { Int($0) }

// Orientation is applied so pixels come out upright; properties are dropped so no
// EXIF/GPS ends up in the output (same rule as the WebP versions).
let loadOptions: [CIImageOption: Any] = [.applyOrientationProperty: true]
guard let sdr = CIImage(contentsOf: source, options: loadOptions),
      let hdr = CIImage(contentsOf: source, options: loadOptions.merging([.expandToHDR: true]) { $1 })
else { fail("cannot read \(source.path)") }

let colorSpace = sdr.colorSpace ?? CGColorSpace(name: CGColorSpace.displayP3)!
let context = CIContext()

func scaled(_ image: CIImage, longEdge: Int) -> CIImage {
    let scale = min(1, CGFloat(longEdge) / max(image.extent.width, image.extent.height))
    guard scale < 1 else { return image }
    return image
        .applyingFilter("CILanczosScaleTransform", parameters: [kCIInputScaleKey: scale, kCIInputAspectRatioKey: 1])
        .settingProperties([:])
}

for edge in edges {
    let out = URL(fileURLWithPath: "\(prefix)-\(edge)-hdr.jpg")
    let options: [CIImageRepresentationOption: Any] = [
        .hdrImage: scaled(hdr, longEdge: edge),
        CIImageRepresentationOption(rawValue: kCGImageDestinationLossyCompressionQuality as String): quality,
    ]
    do {
        try context.writeJPEGRepresentation(of: scaled(sdr, longEdge: edge).settingProperties([:]),
                                            to: out, colorSpace: colorSpace, options: options)
    } catch {
        fail("cannot write \(out.path): \(error)")
    }
}
