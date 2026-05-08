import Foundation

@main
struct TestCommonLib {
    static func main() {
        let data = Data("alpha\nbeta\n".utf8)
        let src = "/tmp/swift-common_lib-src.txt"
        let dst = "/tmp/swift-common_lib-dst.txt"
        do {
            try data.write(to: URL(fileURLWithPath: src))
            FileManager.default.createFile(atPath: dst, contents: nil)
            let out = try FileHandle(forWritingTo: URL(fileURLWithPath: dst))
            defer { try? out.close() }
            try common_lib.copyFile(src, out)
            let got = try Data(contentsOf: URL(fileURLWithPath: dst))
            if got != data { exit(1) }
            try? FileManager.default.removeItem(atPath: src)
            try? FileManager.default.removeItem(atPath: dst)
            exit(0)
        } catch {
            exit(1)
        }
    }
}
