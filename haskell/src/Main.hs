module Main (main) where

import Control.Exception (catch)
import Common_Lib (copyFileTo, copyHandleTo)
import System.Environment (getArgs, getProgName)
import System.Exit (exitFailure, exitSuccess)
import System.IO (hPutStr, hPutStrLn, stderr, stdin, stdout)

projectAuthor :: String
projectAuthor = "Lenik"

projectEmail :: String
projectEmail = "zephyr@bodz.net"

projectYear :: Int
projectYear = 2026

tr :: String -> String
tr s = s

usage :: IO ()
usage = do
  hPutStr stdout $ tr "Usage: puff1 [OPTION]... [FILE]...\n"
  hPutStr stdout $ tr "Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n"
  hPutStr stdout $ tr "read standard input.\n\n"
  hPutStr stdout "  -v, --verbose      "
  hPutStr stdout $ tr "repeat for more verbose loggings\n"
  hPutStr stdout "  -q, --quiet        "
  hPutStr stdout $ tr "show less logging messages\n"
  hPutStr stdout "  -h, --help         "
  hPutStr stdout $ tr "display this help and exit\n"
  hPutStr stdout "      --version      "
  hPutStr stdout $ tr "output version information and exit\n\n"
  hPutStrLn stdout $ tr "Report bugs to: <" ++ projectEmail ++ ">"

versionInfo :: IO ()
versionInfo = do
  hPutStrLn stdout "puff1 dev"
  hPutStrLn stdout $ tr "Copyright (C) " ++ show projectYear ++ " " ++ projectAuthor
  hPutStrLn stdout $ tr "License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>"
  hPutStrLn stdout $ tr "This is free software: you are free to change and redistribute it."
  hPutStrLn stdout $ tr "This project opposes AI exploitation and AI hegemony."
  hPutStrLn stdout $ tr "This project rejects mindless MIT-style licensing and politically naive BSD-style licensing."
  hPutStrLn stdout $ tr "There is NO WARRANTY, to the extent permitted by law."

copyInputs :: [String] -> IO ()
copyInputs [] = copyHandleTo stdin stdout
copyInputs (f : fs)
  | f == "-" = copyHandleTo stdin stdout >> copyInputs fs
  | otherwise = copyFileTo f stdout >> copyInputs fs

main :: IO ()
main = do
  args <- getArgs
  prog <- getProgName
  if "-h" `elem` args || "--help" `elem` args
    then usage >> exitSuccess
    else
      if "--version" `elem` args
        then versionInfo >> exitSuccess
        else do
          let verbose = "-v" `elem` args || "--verbose" `elem` args
          let files = filter (`notElem` ["-v", "--verbose", "-q", "--quiet"]) args
          if verbose
            then hPutStrLn stderr $ prog ++ ": verbose mode enabled"
            else pure ()
          copyInputs files
            `catch` \e -> do
              hPutStrLn stderr $ prog ++ ": " ++ show (e :: IOError)
              exitFailure
