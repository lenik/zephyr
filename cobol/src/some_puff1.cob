      *> Copyright (C) 2026 Lenik <zephyr@bodz.net>
      *> SPDX-License-Identifier: AGPL-3.0-or-later
       IDENTIFICATION DIVISION.
       PROGRAM-ID. some_puff1.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT IN-FILE ASSIGN TO DYNAMIC WS-FILE-NAME
               ORGANIZATION IS LINE SEQUENTIAL
               FILE STATUS IS IN-FILE-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD IN-FILE.
       01 IN-REC PIC X(8192).
       WORKING-STORAGE SECTION.
       01 IN-FILE-STATUS PIC XX.
       01 WS-FILE-NAME    PIC X(512).
       01 WS-ARG-COUNT    PIC 9(4) COMP.
       01 WS-ARG-IDX      PIC 9(4) COMP VALUE 1.
       01 WS-ARG          PIC X(256).
       01 WS-STATUS       PIC 9 VALUE 0.
       01 WS-EOF-FLAG     PIC X VALUE "N".
       01 WS-EOF          PIC 9 COMP VALUE 0.
       01 WS-VERBOSE      PIC S9(4) COMP VALUE 0.
       PROCEDURE DIVISION.
           COPY "commons.cob".
       MAIN-LOGIC.
           PERFORM PARSE-ARGS
           IF WS-STATUS NOT = 0 THEN
               STOP RUN
           END-IF
           IF WS-ARG-COUNT = 0 THEN
               IF WS-VERBOSE > 0 THEN
                   DISPLAY "some_puff1: reading from standard input" UPON SYSERR
               END-IF
               PERFORM COPY-STDIN
               STOP RUN
           END-IF
           PERFORM VARYING WS-ARG-IDX FROM 1 BY 1
               UNTIL WS-ARG-IDX > WS-ARG-COUNT
               ACCEPT WS-ARG FROM ARGUMENT-VALUE WS-ARG-IDX
               IF WS-ARG = "-" THEN
                   PERFORM COPY-STDIN
               ELSE
                   MOVE WS-ARG TO WS-FILE-NAME
                   MOVE "N" TO WS-EOF-FLAG
                   MOVE 0 TO WS-EOF
                   PERFORM COPY-FILE-DATA
                   IF WS-STATUS NOT = 0 THEN
                       STOP RUN RETURNING 1
                   END-IF
               END-IF
           END-PERFORM
           STOP RUN
           .
       PARSE-ARGS.
           ACCEPT WS-ARG-COUNT FROM ARGUMENT-NUMBER
           PERFORM VARYING WS-ARG-IDX FROM 1 BY 1
               UNTIL WS-ARG-IDX > WS-ARG-COUNT
               ACCEPT WS-ARG FROM ARGUMENT-VALUE WS-ARG-IDX
               EVALUATE WS-ARG
                   WHEN "-h" WHEN "--help"
                       PERFORM SHOW-HELP
                       MOVE 1 TO WS-STATUS
                   WHEN "--version"
                       PERFORM SHOW-VERSION
                       MOVE 1 TO WS-STATUS
                   WHEN "-v" WHEN "--verbose"
                       ADD 1 TO WS-VERBOSE
                   WHEN "-q" WHEN "--quiet"
                       MOVE -1 TO WS-VERBOSE
               END-EVALUATE
           END-PERFORM
           .
       SHOW-HELP.
           DISPLAY "Usage: some_puff1 [OPTION]... [FILE]..."
           DISPLAY "  -v, --verbose  -h, --help  --version"
           .
       SHOW-VERSION.
           DISPLAY "some_puff1 dev"
           DISPLAY "Copyright (C) 2026 Lenik"
           .
       COPY-STDIN.
           PERFORM UNTIL WS-EOF
               ACCEPT IN-REC FROM SYSIN AT END
                   MOVE 1 TO WS-EOF
               NOT AT END
                   DISPLAY IN-REC
           END-ACCEPT
           END-PERFORM
           .
       END PROGRAM some_puff1.
