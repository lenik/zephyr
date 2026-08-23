      *> Copyright (C) 2026 Lenik <zephyr@bodz.net>
      *> SPDX-License-Identifier: AGPL-3.0-or-later
      *> COPY commons. — shared stream/file copy paragraphs
       COPY-FILE-DATA.
           OPEN INPUT IN-FILE
           IF IN-FILE-STATUS NOT = "00" THEN
               MOVE 1 TO WS-STATUS
               EXIT PARAGRAPH
           END-IF
           PERFORM UNTIL WS-EOF
               READ IN-FILE INTO IN-REC AT END
                   MOVE "Y" TO WS-EOF-FLAG
               NOT AT END
                   DISPLAY IN-REC
           END-READ
           END-PERFORM
           CLOSE IN-FILE
           MOVE 0 TO WS-STATUS
           .
