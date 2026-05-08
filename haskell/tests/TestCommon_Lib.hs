module Main (main) where

import Common_Lib (copyFileTo)
import System.Directory (removeFile)
import System.IO (hClose, hFlush, hSeek, hTell, IOMode (ReadMode, WriteMode), SeekMode (AbsoluteSeek), openBinaryTempFile, openFile)

main :: IO ()
main = do
  (inPath, inH) <- openBinaryTempFile "/tmp" "puff1-in.txt"
  (outPath, outH) <- openBinaryTempFile "/tmp" "puff1-out.txt"
  hClose inH
  hClose outH
  writeFile inPath "alpha\nbeta\n"
  outHandle <- openFile outPath WriteMode
  copyFileTo inPath outHandle
  hFlush outHandle
  pos <- hTell outHandle
  hSeek outHandle AbsoluteSeek 0
  hClose outHandle
  got <- readFile outPath
  if got == "alpha\nbeta\n" && pos > 0
    then do
      removeFile inPath
      removeFile outPath
    else error "copyFileTo failed"
