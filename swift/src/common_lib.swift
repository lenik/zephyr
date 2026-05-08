import Foundation

enum common_lib {
    static func copyStream(_ input: FileHandle, _ output: FileHandle) throws {
        while true {
            let data = input.readData(ofLength: 65536)
            if data.isEmpty { return }
            output.write(data)
        }
    }

    static func copyFile(_ path: String, _ output: FileHandle) throws {
        let handle = try FileHandle(forReadingFrom: URL(fileURLWithPath: path))
        defer { try? handle.close() }
        try copyStream(handle, output)
    }
}
