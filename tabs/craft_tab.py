"""tabs/craft_tab.py — Calculateur de craft avec détection clic droit Dofus."""
import re, uuid, threading, time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QLineEdit, QFrame, QSpinBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
import model, theme

T = theme
MAX_RES = 8

# ─── Helpers ──────────────────────────────────────────────────────────
def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{T.BORDER};max-height:1px;"); return f

def _lbl(txt, color=None, size="9pt", bold=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{size};"
    if color: ss += f"color:{color};"
    if bold:  ss += "font-weight:bold;"
    l.setStyleSheet(ss); return l

def _inp(placeholder="", w=None):
    e = QLineEdit(); e.setPlaceholderText(placeholder)
    e.setFixedHeight(28)
    if w: e.setFixedWidth(w)
    e.setStyleSheet(
        f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
        f"border-radius:6px;padding:2px 8px;color:{T.TEXT};font-size:9pt;}}"
        f"QLineEdit:focus{{border:1px solid {T.ORANGE};}}")
    return e

def _grad_btn(text, h=30):
    b = QPushButton(text); b.setFixedHeight(h)
    b.setStyleSheet(
        f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
        f"border-radius:7px;font-size:9pt;font-weight:bold;}}"
        f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
        f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});}}")
    b.setCursor(Qt.CursorShape.PointingHandCursor); return b

def _fmt(v): return f"{v:,}".replace(",", " ")
def _parse(t):
    try: return int(re.sub(r'\s', '', str(t)))
    except: return 0

# ─── KamasLineEdit ────────────────────────────────────────────────────
class KamasLineEdit(QLineEdit):
    def __init__(self, p=None):
        super().__init__(p)
        self.setFixedHeight(28)
        self.setPlaceholderText("0")
        self.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:6px;padding:2px 8px;color:{T.TEXT};font-size:9pt;}}"
            f"QLineEdit:focus{{border:1px solid {T.ORANGE};}}")
        self.editingFinished.connect(self._fmt_self)

    def _fmt_self(self):
        v = _parse(self.text())
        self.blockSignals(True)
        self.setText(_fmt(v) if v else "")
        self.blockSignals(False)

    def value(self): return _parse(self.text())
    def setValue(self, v): self.setText(_fmt(v) if v else "")

# ─── ResourceRow ─────────────────────────────────────────────────────
class ResourceRow(QWidget):
    def __init__(self, idx, on_change, parent=None):
        super().__init__(parent)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 2, 0, 2); main.setSpacing(3)

        r1 = QHBoxLayout(); r1.setSpacing(6)
        num = _lbl(f"{idx+1}.", T.HINT, "8pt"); num.setFixedWidth(16)
        r1.addWidget(num)
        self._name = _inp("Nom de la ressource")
        self._name.textChanged.connect(on_change)
        r1.addWidget(self._name, 1)
        del_btn = QPushButton("✕"); del_btn.setFixedSize(26, 26)
        del_btn.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:5px;font-size:10pt;padding:0;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn = del_btn
        r1.addWidget(del_btn)
        main.addLayout(r1)

        r2 = QHBoxLayout(); r2.setSpacing(6); r2.addSpacing(22)
        r2.addWidget(_lbl("Qté :", T.HINT, "8pt"))
        self._qty = QSpinBox(); self._qty.setRange(1, 9999); self._qty.setValue(1)
        self._qty.setFixedHeight(26); self._qty.setFixedWidth(66)
        self._qty.setStyleSheet(
            f"QSpinBox{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:6px;padding:2px 6px;color:{T.TEXT};font-size:9pt;}}"
            f"QSpinBox:focus{{border:1px solid {T.ORANGE};}}"
            f"QSpinBox::up-button{{width:0;border:none;}}"
            f"QSpinBox::down-button{{width:0;border:none;}}")
        self._qty.valueChanged.connect(on_change)
        r2.addWidget(self._qty)
        r2.addWidget(_lbl("Prix/u :", T.HINT, "8pt"))
        self._price = KamasLineEdit(); self._price.setFixedWidth(110)
        self._price.textChanged.connect(on_change)
        r2.addWidget(self._price)
        r2.addStretch()
        main.addLayout(r2)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{T.BORDER};max-height:1px;")
        main.addWidget(sep)

    def data(self):
        return {"name": self._name.text().strip(),
                "qty": self._qty.value(), "price": self._price.value()}

    def load(self, d):
        self._name.setText(d.get("name", ""))
        self._qty.setValue(d.get("qty", 1))
        self._price.setValue(d.get("price", 0))

    def set_name(self, n): self._name.setText(n)

# ─── CraftCard ───────────────────────────────────────────────────────
class CraftCard(QFrame):
    def __init__(self, data, on_save, on_delete, parent=None):
        super().__init__(parent)
        self._data = data; self._on_save = on_save; self._on_delete = on_delete
        self._rows = []; self._collapsed = False
        self.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};border-radius:10px;}}"
            f"QLabel{{background:transparent;border:none;}}")
        self._build(); self._refresh_result()

    def _build(self):
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(12, 10, 12, 12); self._lay.setSpacing(6)

        hdr = QHBoxLayout(); hdr.setSpacing(8)
        self._name_inp = _inp("Nom du craft")
        self._name_inp.setText(self._data.get("name", ""))
        self._name_inp.setStyleSheet(
            f"QLineEdit{{background:transparent;border:none;"
            f"border-bottom:1px solid {T.BORDER};border-radius:0;"
            f"color:{T.TEXT};font-size:10pt;font-weight:bold;padding:2px 4px;}}"
            f"QLineEdit:focus{{border-bottom:1px solid {T.ORANGE};}}")
        self._name_inp.textChanged.connect(self._save)
        hdr.addWidget(self._name_inp, 1)

        self._cb = QPushButton("▾"); self._cb.setFixedSize(24, 24)
        self._cb.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.HINT};"
            f"border:none;font-size:11pt;padding:0;}}"
            f"QPushButton:hover{{color:{T.TEXT};}}")
        self._cb.clicked.connect(self._toggle); hdr.addWidget(self._cb)

        db = QPushButton("🗑"); db.setFixedSize(24, 24)
        db.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.HINT};"
            f"border:none;font-size:10pt;padding:0;}}"
            f"QPushButton:hover{{color:{T.RED};}}")
        db.setCursor(Qt.CursorShape.PointingHandCursor)
        db.clicked.connect(self._on_delete); hdr.addWidget(db)
        self._lay.addLayout(hdr); self._lay.addWidget(_sep())

        self._body = QWidget()
        bl = QVBoxLayout(self._body)
        bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(2)

        self._res_lay = QVBoxLayout(); self._res_lay.setSpacing(0)
        bl.addLayout(self._res_lay)

        self._add_btn = QPushButton("+ Ajouter une ressource")
        self._add_btn.setFixedHeight(26)
        self._add_btn.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px dashed {T.BORDER};border-radius:6px;font-size:8pt;}}"
            f"QPushButton:hover{{color:{T.ORANGE};border-color:{T.ORANGE};}}")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(lambda: self._add_row())
        bl.addWidget(self._add_btn); bl.addWidget(_sep())

        for attr, lbl_txt, color, is_inp in [
            ("_hotel_inp", "Prix hôtel de vente", T.BLUE,   True),
            ("_cost_lbl",  "Coût de craft",        T.ORANGE, False),
            ("_margin_lbl","Marge",                T.TEXT,   False),
        ]:
            box = QFrame()
            box.setStyleSheet(
                f"QFrame{{background:{T.BG_DARK};border-radius:8px;border:none;}}"
                f"QLabel{{background:transparent;border:none;}}")
            brow = QHBoxLayout(box); brow.setContentsMargins(12, 8, 12, 8)
            brow.addWidget(_lbl(lbl_txt, T.HINT, "8pt")); brow.addStretch()
            if is_inp:
                w = KamasLineEdit(); w.setFixedWidth(160)
                w.setValue(self._data.get("hotel_price", 0))
                w.setStyleSheet(
                    f"QLineEdit{{background:transparent;border:none;"
                    f"color:{color};font-size:12pt;font-weight:bold;padding:0;}}"
                    f"QLineEdit:focus{{border-bottom:1px solid {color};}}")
                w.textChanged.connect(self._refresh_result)
                w.textChanged.connect(self._save)
            else:
                w = QLabel("0")
                w.setStyleSheet(
                    f"color:{color};font-size:12pt;font-weight:bold;background:transparent;")
                w.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            setattr(self, attr, w); brow.addWidget(w); bl.addWidget(box)

        self._lay.addWidget(self._body)
        for r in self._data.get("resources", []): self._add_row(r)
        if not self._rows: self._add_row()

    def _add_row(self, data=None):
        if len(self._rows) >= MAX_RES: return
        row = ResourceRow(len(self._rows), self._refresh_result)
        if data: row.load(data)
        row.del_btn.clicked.connect(lambda checked=False, r=row: self._del_row(r))
        self._res_lay.addWidget(row); self._rows.append(row)
        self._add_btn.setVisible(len(self._rows) < MAX_RES); self._save()

    def _del_row(self, row):
        for i, r in enumerate(self._rows):
            if r is row:
                self._res_lay.removeWidget(r); r.deleteLater()
                self._rows.pop(i); break
        self._add_btn.setVisible(len(self._rows) < MAX_RES)
        self._refresh_result(); self._save()

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)
        self._cb.setText("▸" if self._collapsed else "▾")

    def _refresh_result(self):
        cost = sum(r.data()["qty"] * r.data()["price"] for r in self._rows)
        hotel = self._hotel_inp.value()
        margin = hotel - cost
        color = T.GREEN if margin >= 0 else T.RED
        self._cost_lbl.setText(_fmt(cost))
        self._margin_lbl.setText(("+" if margin >= 0 else "") + _fmt(abs(margin)))
        self._margin_lbl.setStyleSheet(
            f"color:{color};font-size:12pt;font-weight:bold;background:transparent;")
        self._save()

    def _save(self):
        self._data["name"] = self._name_inp.text()
        self._data["resources"] = [r.data() for r in self._rows]
        self._data["hotel_price"] = self._hotel_inp.value()
        self._on_save()

    def fill_first_empty(self, name):
        """Rempli la première ligne vide. Retourne True si réussi."""
        for row in self._rows:
            if not row.data()["name"]:
                row.set_name(name); return True
        if len(self._rows) < MAX_RES:
            self._add_row(); self._rows[-1].set_name(name); return True
        return False

# ─── OCR de la zone sombre du menu ───────────────────────────────────
def _ocr_menu(x, y):
    """
    Screenshot → localise 'Insérer dans le chat' via Windows OCR
    → extrait les lignes AU-DESSUS (= nom de la ressource)
    → inversion + upscale bilinéaire → OCR du nom.
    """
    import os, asyncio, io as _io

    try:
        from PIL import ImageGrab, Image as PILImage, ImageOps, ImageFilter
        import numpy as np

        region = (max(0, x - 5), max(0, y - 5), x + 700, y + 200)
        img = ImageGrab.grab(bbox=region).convert("RGB")

        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.globalization import Language
        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

        async def _ocr_full(pil_img):
            eng = None
            try: eng = OcrEngine.try_create_from_language(Language("fr-FR"))
            except: pass
            if not eng:
                try: eng = OcrEngine.try_create_from_user_profile_languages()
                except: pass
            if not eng: return None

            bmp = _io.BytesIO(); pil_img.convert("RGB").save(bmp, format="BMP")
            stream = InMemoryRandomAccessStream()
            wr = DataWriter(stream.get_output_stream_at(0))
            wr.write_bytes(bmp.getvalue())
            await wr.store_async(); wr.detach_stream(); stream.seek(0)
            dec = await BitmapDecoder.create_async(stream)
            sb  = await dec.get_software_bitmap_async()
            return await eng.recognize_async(sb)

        # ── Étape 1 : OCR complète pour trouver Y de "Insérer" ──────
        try:
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
            result = _loop.run_until_complete(_ocr_full(img))
        finally:
            try: _loop.close()
            except: pass
        if not result or not result.lines:
            return None

        inserer_y = None
        for line in result.lines:
            if "ins" in line.text.lower() and line.words:
                inserer_y = line.words[0].bounding_rect.y
                break

        if inserer_y is None:
            # Fallback : texte complet avant "Insérer"
            full = result.text.strip()
            for m in ["Insérer", "insérer", "Recettes"]:
                if m in full:
                    name = re.sub(r'^[^a-zA-ZÀ-ÿ]+', '',
                                  full[:full.index(m)]).strip()
                    if len(name) > 2:
                        return name
            return None

        # ── Étape 2 : extraire les lignes AU-DESSUS de "Insérer" ────
        header_bottom = int(inserer_y) - 2
        header_top    = max(0, header_bottom - 55)
        menu_w = min(380, img.width)
        header = img.crop((8, header_top, menu_w, header_bottom))

        # Niveaux de gris → inverser (texte blanc→noir, fond sombre→clair)
        from PIL import ImageEnhance
        header_gray = header.convert("L")
        header_inv  = header_gray.point(lambda p: 255 - p)

        # Fort contraste pour séparer texte et fond
        header_inv = ImageEnhance.Contrast(header_inv).enhance(4.0)

        # ×6 bilinéaire : lisse suffisamment sans déformer
        header = header_inv.convert("RGB").resize(
            (header_inv.width * 6, header_inv.height * 6),
            PILImage.Resampling.BILINEAR)

        # ── Étape 3 : pytesseract sur le header (meilleur sur pixel font) ──
        raw2 = ""
        try:
            import pytesseract
            import os as _os
            for tp in [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]:
                if _os.path.exists(tp):
                    pytesseract.pytesseract.tesseract_cmd = tp
                    break
            raw2 = pytesseract.image_to_string(
                header,
                lang="fra+eng",
                config="--psm 6 --oem 3 --dpi 300"
            ).strip()
            # Prendre la première ligne non vide
            lines = [l.strip() for l in raw2.splitlines() if l.strip()]
            raw2 = lines[0] if lines else ""
        except Exception as e_tess:
            # Fallback Windows OCR
            try:
                try:
                    _loop2 = asyncio.new_event_loop()
                    asyncio.set_event_loop(_loop2)
                    result2 = _loop2.run_until_complete(_ocr_full(header))
                finally:
                    try: _loop2.close()
                    except: pass
                raw2 = result2.text.strip() if result2 else ""
            except Exception:
                raw2 = ""

        name = re.sub(r'^[^a-zA-ZÀ-ÿ]+', '', raw2).strip()
        name = re.sub(r'\s+', ' ', name).strip()
        name = name.split('\n')[0].strip()
        # Supprimer les mots parasites courts en début (artefacts OCR)
        words = name.split()
        while words and len(words[0]) <= 2:
            words.pop(0)
        name = " ".join(words).strip()
        if len(name) > 2:
            return name

        # ── Fallback : texte full-image avant "Insérer" ─────────────
        full = result.text.strip()
        for m in ["Insérer", "insérer", "Recettes", "recettes"]:
            if m in full:
                candidate = re.sub(r'^[^a-zA-ZÀ-ÿ]+', '',
                                   full[:full.index(m)]).strip()
                candidate = re.sub(r'\s+', ' ', candidate).strip()
                if len(candidate) > 2:
                    return candidate
                break

        # ── Fallback 2 : lignes OCR avant "Insérer" ─────────────────
        for line in result.lines:
            line_y = line.words[0].bounding_rect.y if line.words else 9999
            if line_y < inserer_y - 5:
                candidate = re.sub(r'^[^a-zA-ZÀ-ÿ]+', '',
                                   line.text).strip()
                if len(candidate) > 2:
                    return candidate

    except Exception:
        pass

    return None

# ─── CraftTab ─────────────────────────────────────────────────────────
class CraftTab(QWidget):
    _name_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._crafts = []; self._cards = []; self._watching = False
        self._build(); self._load()
        self._name_signal.connect(self._on_name)
        self._start_watcher()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;}}"
            f"QLabel{{background:transparent;color:white;border:none;}}")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(14, 0, 12, 0); hl.setSpacing(8)
        t = QLabel("🔧  Craft")
        t.setStyleSheet("font-size:11pt;font-weight:bold;color:white;background:transparent;")
        hl.addWidget(t); hl.addStretch(); lay.addWidget(hdr)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea{{background:{T.BG};}}")
        container = QWidget(); container.setStyleSheet(f"background:{T.BG};")
        self._cards_lay = QVBoxLayout(container)
        self._cards_lay.setContentsMargins(10, 10, 10, 10); self._cards_lay.setSpacing(8)
        self._cards_lay.addStretch()
        scroll.setWidget(container); lay.addWidget(scroll, 1)

        footer = QFrame()
        footer.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};"
            f"border-top:1px solid {T.BORDER};border-radius:0;}}")
        fl = QVBoxLayout(footer); fl.setContentsMargins(10, 10, 10, 10); fl.setSpacing(8)

        info = QFrame()
        info.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border:1px solid {T.BORDER};"
            f"border-radius:8px;}}"
            f"QLabel{{background:transparent;border:none;}}")
        il = QHBoxLayout(info); il.setContentsMargins(12, 10, 12, 10); il.setSpacing(10)
        icon = QLabel("🖱"); icon.setStyleSheet("font-size:18pt;background:transparent;")
        il.addWidget(icon)
        desc = QLabel(
            "Fais un clic droit sur une ressource dans Dofus —\n"
            "le nom est automatiquement rempli dans le premier champ vide.")
        desc.setStyleSheet(f"color:{T.SUBTEXT};font-size:9pt;background:transparent;")
        desc.setWordWrap(True); il.addWidget(desc, 1)
        fl.addWidget(info)

        self._status = QLabel("")
        self._status.setStyleSheet(
            f"color:{T.ORANGE};font-size:9pt;font-weight:bold;"
            f"background:transparent;padding:2px 4px;")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setVisible(False); fl.addWidget(self._status)

        add_btn = _grad_btn("＋  Nouveau craft", 36)
        add_btn.clicked.connect(self._new_craft); fl.addWidget(add_btn)
        lay.addWidget(footer)

    def _start_watcher(self):
        self._watching = True
        self._active   = True
        threading.Thread(target=self._watch_loop, daemon=True).start()

    def set_active(self, active: bool):
        self._active = active

    def _watch_loop(self):
        try:
            import win32api, win32con, win32gui
            prev = False; dofus_ok = False; px = py = 0
            while self._watching:
                state = win32api.GetAsyncKeyState(win32con.VK_RBUTTON)
                cur   = bool(state & 0x8000)

                if cur and not prev:
                    try:
                        px, py = win32api.GetCursorPos()
                        hwnd   = win32gui.WindowFromPoint((px, py))
                        while True:
                            p = win32gui.GetParent(hwnd)
                            if not p: break
                            hwnd = p
                        title  = win32gui.GetWindowText(hwnd).lower()
                        dofus_ok = ("dofus" in title and "toolbox" not in title)
                    except:
                        dofus_ok = False

                if not cur and prev and dofus_ok:
                    dofus_ok = False
                    if self._active:
                        cx, cy = px, py
                        try:
                            time.sleep(0.22)
                            name = _ocr_menu(cx, cy)
                            if name:
                                self._name_signal.emit(name)
                        except:
                            pass

                prev = cur
                time.sleep(0.02)
        except Exception:
            pass

    def _on_name(self, name):
        from PySide6.QtCore import QTimer
        QApplication.clipboard().setText(name)
        filled = False
        for card in self._cards:
            if card.fill_first_empty(name):
                filled = True
                break
        self._status.setText(f"✓  {name}")
        self._status.setVisible(True)
        QTimer.singleShot(4000, lambda: self._status.setVisible(False))

    def _new_craft(self):
        d = {"id": str(uuid.uuid4()), "name": "", "resources": [], "hotel_price": 0}
        self._crafts.append(d); self._add_card(d); self._save()

    def _add_card(self, d):
        c = CraftCard(d, self._save, lambda _=None, dd=d: self._del_craft(dd))
        self._cards_lay.insertWidget(self._cards_lay.count() - 1, c)
        self._cards.append(c)

    def _del_craft(self, d):
        for i, c in enumerate(self._crafts):
            if c.get("id") == d.get("id"):
                self._crafts.pop(i)
                card = self._cards.pop(i)
                self._cards_lay.removeWidget(card)
                card.deleteLater()
                break
        self._save()

    def _load(self):
        for d in model.load_config().get("crafts", []):
            self._crafts.append(d); self._add_card(d)

    def _save(self):
        cfg = model.load_config(); cfg["crafts"] = self._crafts; model.save_config(cfg)

    def closeEvent(self, e):
        self._watching = False; super().closeEvent(e)
