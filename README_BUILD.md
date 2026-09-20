# คู่มือ Build ShareWebAndFiles.exe

## สิ่งที่ตรวจสอบให้แล้ว
อ่านโค้ดทั้ง `ui.py`, `app.py`, `core.py` แล้ว และลอง **build จริง** ด้วย PyInstaller
(รันบน Linux sandbox ของ Claude เอง เพื่อเช็ค recipe ก่อนส่งให้ ไม่ได้เดาจากความจำ)
เจอปัญหาที่พบบ่อยกับ customtkinter คือถ้าไม่รวมไฟล์ theme/icon (`assets/`) เข้าไปด้วย
แอปจะ crash ทันทีตอนเปิด (`FileNotFoundError` ตอนโหลด theme) — spec file ที่แนบมาแก้ปัญหานี้ไว้แล้ว
และทดสอบรันไฟล์ที่ build ได้จริงผ่าน virtual display จนแอปขึ้นสำเร็จและอยู่ใน event loop
ได้ปกติโดยไม่มี error

## ทำไมไม่ได้ .exe ให้เลยในแชทนี้
Claude รันอยู่บน Linux sandbox — PyInstaller **ไม่ cross-compile ข้าม OS** (ต้องรันบน Windows
เท่านั้นถึงจะได้ .exe, รันบน Linux ได้แค่ ELF binary ของ Linux) จึงเตรียมไฟล์ build ที่ผ่านการทดสอบ
ไว้ให้ครบ พร้อม 2 ทางเลือกด้านล่างเพื่อให้ได้ .exe จริง

## ไฟล์ที่แนบมา
| ไฟล์ | หน้าที่ |
|---|---|
| `ShareWebAndFiles.spec` | สูตร build ของ PyInstaller (ตั้งค่าลด false-positive ไว้แล้ว) |
| `version_info.txt` | ข้อมูล version/publisher ที่ฝังใน .exe |
| `.github/workflows/build-windows.yml` | ให้ GitHub build ให้อัตโนมัติบนเครื่อง Windows จริง ฟรี |
| ไฟล์นี้ | คู่มือ |

นำไฟล์เหล่านี้ไปวางรวมกับ `app.py`, `ui.py`, `core.py`, `requirements.txt` ในโฟลเดอร์เดียวกัน
(โครงสร้าง `.github/workflows/...` ต้องอยู่ตาม path เดิม)

## ทางเลือกที่ 1: ให้ GitHub build ให้ (แนะนำถ้าไม่มีเครื่อง Windows)
1. สร้าง repo บน GitHub (public/private ก็ได้ Actions ใช้ฟรีทั้งคู่)
2. อัปโหลดไฟล์ทั้งหมดข้างต้นเข้า repo แล้ว push
3. ไปแท็บ **Actions** → รอ workflow "Build Windows exe" รันเสร็จ (~2-3 นาที) หรือกด
   "Run workflow" เพื่อสั่งรันเองก็ได้
4. ดาวน์โหลด artifact ชื่อ `ShareWebAndFiles-windows` (.zip) จากหน้าผลลัพธ์ของ run นั้น
5. แตกไฟล์แล้วรัน `ShareWebAndFiles.exe` ได้เลย — **ต้องอยู่กับโฟลเดอร์ `_internal` เสมอ**
   ห้ามแยก .exe ออกไปรันเดี่ยวๆ

## ทางเลือกที่ 2: Build เองบนเครื่อง Windows
1. ติดตั้ง Python 3.10+ (จาก python.org)
2. เปิด Command Prompt ไปที่โฟลเดอร์โปรเจกต์
3. รัน:
   ```
   pip install -r requirements.txt pyinstaller
   pyinstaller ShareWebAndFiles.spec
   ```
4. ได้ไฟล์ที่ `dist\ShareWebAndFiles\ShareWebAndFiles.exe`

## เรื่อง Windows Defender / SmartScreen ฟ้องว่าเป็นไวรัส
ขอพูดตรงๆ ก่อน: **ไม่มีวิธีไหนรับประกันได้ 100% ว่าจะไม่โดน** ถ้าไฟล์ยังไม่ได้เซ็นดิจิทัล และผมช่วย
เขียนโค้ดที่จงใจซ่อนพฤติกรรมจากโปรแกรมป้องกันไวรัส (เข้ารหัส payload, เช็ค sandbox แล้วเปลี่ยนพฤติกรรม
ฯลฯ) ไม่ได้ เพราะเป็นเทคนิคเดียวกับที่มัลแวร์ใช้จริง — สิ่งที่ทำได้และช่วยได้จริงคือแนวทางมาตรฐานพวกนี้
(เรียงจากได้ผลมากไปน้อย):

1. **Code sign ไฟล์ .exe** — ได้ผลที่สุด ต้องซื้อ Code Signing Certificate จากผู้ให้บริการอย่าง
   DigiCert / SSL.com / Sectigo แบบ EV จะได้ reputation กับ SmartScreen ทันที ส่วนแบบ OV ธรรมดา
   จะค่อยๆ สร้าง reputation ตามยอดดาวน์โหลด
2. **ใช้ onedir แทน onefile** (ตั้งไว้ให้แล้วใน spec) — onefile จะแตกไฟล์ตัวเองลง temp โฟลเดอร์
   ตอนรัน ซึ่งพฤติกรรมนี้คล้าย dropper ของมัลแวร์มาก เป็นสาเหตุอันดับ 1 ที่ PyInstaller โดนตีบ่อย
3. **ปิด UPX compression** (`--noupx`, ตั้งไว้ให้แล้ว) — ไฟล์ที่บีบด้วย UPX มักโดนสงสัยเพราะมัลแวร์
   ก็ใช้ UPX บีบเพื่อเลี่ยงการสแกนลายเซ็นเหมือนกัน
4. **ใส่ version info / publisher metadata** (ทำไว้แล้วใน `version_info.txt`) — .exe ที่ไม่มีข้อมูล
   เวอร์ชัน/ผู้ผลิตเลยจะดูน่าสงสัยกว่า
5. **ส่งไฟล์ให้ Microsoft ตรวจ** — ถ้า build เสร็จแล้วโดน Defender ฟ้อง ส่งไฟล์ไปที่
   `microsoft.com/en-us/wdsi/filesubmission` เลือกหมวด "Software developer" แจ้งว่าเป็น false
   positive ปกติใช้เวลาตรวจ 1-2 วัน ถ้าผ่านจะอัปเดต definition ให้ทั่วโลก
6. **รอสร้าง reputation** — SmartScreen นับจำนวนคนที่รันไฟล์นี้แล้วไม่มีปัญหาเป็นส่วนหนึ่งของการ
   ตัดสินใจ แอปใหม่ที่มีคนโหลดน้อยจะโดนเตือนบ่อยกว่าช่วงแรก แล้วจะลดลงเองเมื่อมีคนใช้มากขึ้น

**ทำไมแอปนี้เสี่ยงกว่าค่าเฉลี่ย:** ตัวแอปดาวน์โหลด `cloudflared.exe` มารันเอง เปิด network port
และเปิด subprocess แบบซ่อนหน้าต่าง console — ทั้งหมดนี้ถูกต้องตามการออกแบบของแอป แต่ตรงกับ
heuristic ที่ AV ใช้เช็คพฤติกรรม dropper/backdoor พอดี ต่อให้ทำครบข้อ 2-4 ก็ยังมีโอกาสโดนเตือนได้
โดยเฉพาะช่วงแรกก่อน Microsoft จะ whitelist ให้ — ทางที่การันตีผลได้จริงมีแค่ code signing +
เวลา/reputation เท่านั้น

## หมายเหตุเรื่องชื่อไฟล์
ในคำขอพิมพ์ว่า `hareWebAndFiles.exe` — ตีความว่าน่าจะพิมพ์ตกตัว "S" (เพราะโค้ดตั้งชื่อคลาสว่า
`ShareApp` และหัวข้อในแอปคือ "Share Web Files") จึงตั้งชื่อ build เป็น **ShareWebAndFiles.exe**
ถ้าต้องการชื่ออื่น แก้ที่บรรทัด `name=` ใน `ShareWebAndFiles.spec` และในไฟล์
`build-windows.yml` (สองจุด: `name:` ของ artifact และ path ที่อ้างอิง) ให้ตรงกัน
