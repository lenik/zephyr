module Common_Lib (copyFileTo, copyHandleTo) where

import qualified Data.ByteString as BS
import System.IO (Handle)

copyHandleTo :: Handle -> Handle -> IO ()
copyHandleTo input output = do
  bs <- BS.hGetContents input
  BS.hPut output bs

copyFileTo :: FilePath -> Handle -> IO ()
copyFileTo path output = do
  bs <- BS.readFile path
  BS.hPut output bs
