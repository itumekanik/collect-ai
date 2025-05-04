import tkinter as tk
import pyautogui
import os
from PIL import Image, ImageTk
import datetime
from tkinter import messagebox, simpledialog
import time

class ScreenCapture:
    def __init__(self, root):
        self.root = root
        self.root.title("Ekran Yakalama ve YOLO Etiketleme Programı v1.1") # Başlık güncellendi
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.configure(cursor="cross")

        # ----- Durum Değişkenleri -----
        self.mode = 'idle'
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.target_region = None
        self.potential_target_coords = None
        self.target_rect_id = None
        self.annotation_rects_ids = []
        self.overlay_rect_ids = []
        self.current_target_basename = None
        # Son yapılan işaretleme bilgilerini saklamak için (Geri Alma işlemi için)
        self.last_annotation_details = None # {'img_path': ..., 'lbl_path': ..., 'lbl_line': ..., 'canvas_id': ...}

        # ----- Klasör Yönetimi -----
        self.main_folder = "ekran_goruntusu"
        self.target_image_folder = os.path.join(self.main_folder, "images")
        self.labels_folder = os.path.join(self.main_folder, "labels")
        self.annotation_subfolder = ""
        self.annotation_subfolder_path = ""
        self.last_annotation_subfolder = ""
        self.setup_base_folders()

        # ----- Arayüz Elemanları -----
        self.canvas = tk.Canvas(root, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.control_frame = tk.Frame(root, bg="#DDDDDD")
        self.control_frame.place(relx=0.5, rely=1.0, anchor='s', width=800)

        self.status_label = tk.Label(self.control_frame, text="Durum: Başlatıldı. Hedef bölge seçmek için 'W' tuşuna basın.", bg="#DDDDDD", wraplength=780)
        self.status_label.pack(pady=5, padx=10, fill=tk.X)

        self.subfolder_label = tk.Label(self.control_frame, text="Etiket Sınıfı (Klasör): Seçilmedi ('A' tuşu)", bg="#DDDDDD")
        self.subfolder_label.pack(pady=(0,5), padx=10, fill=tk.X)

        # ----- Olayları Bağla -----
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.root.bind("<KeyPress-w>", self.enter_target_selection_mode)
        self.root.bind("<KeyPress-W>", self.enter_target_selection_mode)
        self.root.bind("<KeyPress-s>", self.confirm_target_region)
        self.root.bind("<KeyPress-S>", self.confirm_target_region)
        self.root.bind("<KeyPress-a>", self.prompt_annotation_subfolder)
        self.root.bind("<KeyPress-A>", self.prompt_annotation_subfolder)
        self.root.bind("<KeyPress-z>", self.undo_last_annotation) # Geri alma tuşu
        self.root.bind("<KeyPress-Z>", self.undo_last_annotation) # Geri alma tuşu
        self.root.bind("<Escape>", self.exit_program)

    def setup_base_folders(self):
        os.makedirs(self.main_folder, exist_ok=True)
        os.makedirs(self.target_image_folder, exist_ok=True)
        os.makedirs(self.labels_folder, exist_ok=True)

    def setup_annotation_subfolder(self, subfolder_name):
        path = os.path.join(self.main_folder, subfolder_name)
        os.makedirs(path, exist_ok=True)
        return path

    # ----- Mod Değiştirme Fonksiyonları -----

    def enter_target_selection_mode(self, event=None):
        self.mode = 'selecting_target'
        self.target_region = None
        self.potential_target_coords = None
        self.current_target_basename = None
        self.last_annotation_details = None # Yeni hedefte geri alınacak bir şey yok
        self.root.attributes('-alpha', 0.1)
        self.root.configure(cursor="cross")
        self.clear_canvas()
        self.status_label.config(text="Durum: Hedef Bölge Seçimi. Alanı çizip bırakın. Bitince 'S' tuşuna basın.")
        if self.target_rect_id:
             self.canvas.delete(self.target_rect_id)
             self.target_rect_id = None

    def confirm_target_region(self, event=None):
        if self.mode != 'selecting_target' or not self.potential_target_coords:
            messagebox.showwarning("Uyarı", "Önce 'W' tuşuna basıp bir hedef bölge çizmelisiniz.")
            return

        x1, y1, x2, y2 = self.potential_target_coords
        self.target_region = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

        if self.target_rect_id:
            self.canvas.delete(self.target_rect_id)
            self.target_rect_id = None

        self.root.attributes('-alpha', 0.0)
        self.root.update()
        time.sleep(0.2)

        try:
            tx1, ty1, tx2, ty2 = self.target_region
            width = tx2 - tx1
            height = ty2 - ty1
            if width <= 0 or height <= 0:
                 raise ValueError("Hedef bölge genişliği veya yüksekliği sıfır veya negatif olamaz.")

            screenshot = pyautogui.screenshot(region=(tx1, ty1, width, height))
            file_name = self.generate_filename(self.target_image_folder, 5, ".jpg")
            file_path = os.path.join(self.target_image_folder, file_name)
            screenshot.save(file_path)

            self.current_target_basename = os.path.splitext(file_name)[0]
            self.mode = 'annotating'
            label_file_path_display = os.path.join(self.labels_folder, f"{self.current_target_basename}.txt")
            self.status_label.config(text=f"Durum: İşaretleme Modu. Hedef: {file_path} (Etiket: {label_file_path_display}). Sınıf seç ('A'), işaretle ('Z' Geri Al).")
            self.root.configure(cursor="cross")

            self.root.attributes('-alpha', 0.01)
            self.draw_overlay()
            self.root.attributes('-alpha', 0.3)

        except Exception as e:
            messagebox.showerror("Hata", f"Hedef bölge kaydedilirken hata oluştu: {str(e)}")
            self.root.attributes('-alpha', 0.3)
            self.mode = 'idle'
            self.target_region = None
            self.current_target_basename = None
            self.status_label.config(text="Durum: Hata oluştu. Tekrar deneyin.")
        finally:
             if self.root.attributes('-alpha') == 0.0:
                 self.root.attributes('-alpha', 0.3)

    def prompt_annotation_subfolder(self, event=None):
        if self.mode != 'annotating':
             messagebox.showinfo("Bilgi", "Etiket sınıfı (klasör) seçmek için önce bir hedef bölge belirlemelisiniz ('W' -> çiz -> 'S').")
             return

        original_alpha = self.root.attributes('-alpha')
        self.root.attributes('-alpha', 1.0)
        new_subfolder = simpledialog.askstring("Etiket Sınıfı / Alt Klasör",
                                          "İşaretlemelerin kaydedileceği alt klasör ADI GİRİN (Bu aynı zamanda YOLO sınıf adı olacak, boşluksuz):",
                                          initialvalue=self.last_annotation_subfolder,
                                          parent=self.root)
        self.root.attributes('-alpha', original_alpha)

        if new_subfolder and new_subfolder.strip():
            clean_subfolder = new_subfolder.strip().replace(" ", "_")
            if " " in new_subfolder.strip():
                 messagebox.showwarning("Uyarı", f"Boşluklar alt çizgi ile değiştirildi: '{clean_subfolder}'")

            self.annotation_subfolder = clean_subfolder
            self.last_annotation_subfolder = self.annotation_subfolder
            try:
                self.annotation_subfolder_path = self.setup_annotation_subfolder(self.annotation_subfolder)
                self.subfolder_label.config(text=f"Etiket Sınıfı (Klasör): {self.annotation_subfolder}")
                self.status_label.config(text=f"Durum: İşaretleme Modu. Sınıf '{self.annotation_subfolder}' olarak ayarlandı. İşaretlemek için sürükleyin ('Z' Geri Al).")
            except Exception as e:
                 messagebox.showerror("Hata", f"Alt klasör '{self.annotation_subfolder}' oluşturulurken/ayarlanırken hata: {str(e)}")
                 self.annotation_subfolder = ""
                 self.annotation_subfolder_path = ""
                 self.subfolder_label.config(text="Etiket Sınıfı (Klasör): Hata oluştu!")
        elif new_subfolder is not None:
             messagebox.showerror("Hata", "Etiket sınıfı (klasör adı) boş olamaz!")

    # ----- Çizim ve Overlay Fonksiyonları -----

    def draw_overlay(self):
        self.clear_overlay()
        if not self.target_region: return
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x1, y1, x2, y2 = self.target_region
        overlay_color = 'gray50'
        if y1 > 0: self.overlay_rect_ids.append(self.canvas.create_rectangle(0, 0, screen_width, y1, fill=overlay_color, outline=""))
        if y2 < screen_height: self.overlay_rect_ids.append(self.canvas.create_rectangle(0, y2, screen_width, screen_height, fill=overlay_color, outline=""))
        if x1 > 0: self.overlay_rect_ids.append(self.canvas.create_rectangle(0, y1, x1, y2, fill=overlay_color, outline=""))
        if x2 < screen_width: self.overlay_rect_ids.append(self.canvas.create_rectangle(x2, y1, screen_width, y2, fill=overlay_color, outline=""))
        try: # Canvas henüz hazır değilse hata verebilir, nadir durum.
            self.canvas.lower(self.overlay_rect_ids)
        except tk.TclError:
            pass # Başlangıçta olabilir, görmezden gel

    def clear_overlay(self):
        for rect_id in self.overlay_rect_ids: self.canvas.delete(rect_id)
        self.overlay_rect_ids = []

    def clear_annotations(self):
        for rect_id in self.annotation_rects_ids: self.canvas.delete(rect_id)
        self.annotation_rects_ids = []

    def clear_canvas(self):
         self.clear_overlay()
         self.clear_annotations()
         if self.target_rect_id:
             self.canvas.delete(self.target_rect_id)
             self.target_rect_id = None

    # ----- Fare Olayları Yönetimi -----

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.mode == 'selecting_target':
            if self.target_rect_id: self.canvas.delete(self.target_rect_id)
            self.target_rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2, dash=(5, 5))
        elif self.mode == 'annotating':
            if not self.annotation_subfolder:
                 messagebox.showinfo("Bilgi", "İşaretleme yapmadan önce 'A' tuşu ile bir etiket sınıfı (klasör) seçmelisiniz.")
                 self.start_x, self.start_y = None, None
                 return
            # Daha kalın çizim (width=3)
            self.current_annotation_rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='blue', width=3)

    def on_mouse_drag(self, event):
        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)
        if self.start_x is None or self.start_y is None: return
        if self.mode == 'selecting_target' and self.target_rect_id:
            self.canvas.coords(self.target_rect_id, self.start_x, self.start_y, self.current_x, self.current_y)
        elif self.mode == 'annotating' and self.current_annotation_rect_id:
            self.canvas.coords(self.current_annotation_rect_id, self.start_x, self.start_y, self.current_x, self.current_y)

    def on_button_release(self, event):
        if self.start_x is None or self.start_y is None: return

        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        if abs(x1 - x2) < 1 or abs(y1 - y2) < 1:
            if self.mode == 'selecting_target' and self.target_rect_id: self.canvas.delete(self.target_rect_id); self.target_rect_id = None
            elif self.mode == 'annotating' and self.current_annotation_rect_id: self.canvas.delete(self.current_annotation_rect_id); self.current_annotation_rect_id = None
            self.start_x, self.start_y = None, None
            return

        if self.mode == 'selecting_target':
            self.potential_target_coords = (int(x1), int(y1), int(x2), int(y2))
            self.status_label.config(text="Durum: Hedef Bölge Seçildi. Onaylamak için 'S', yeniden seçmek için 'W'.")

        elif self.mode == 'annotating':
            if not self.current_target_basename:
                 messagebox.showerror("Hata", "Aktif bir hedef resim bulunamadı. Lütfen 'W' ve 'S' ile tekrar hedef belirleyin.")
                 if self.current_annotation_rect_id: self.canvas.delete(self.current_annotation_rect_id); self.current_annotation_rect_id = None
                 self.start_x, self.start_y = None, None
                 return
            if not self.annotation_subfolder:
                 messagebox.showinfo("Bilgi", "Lütfen önce 'A' tuşuna basarak bir etiket sınıfı (klasör) seçin.")
                 if self.current_annotation_rect_id: self.canvas.delete(self.current_annotation_rect_id); self.current_annotation_rect_id = None
                 self.start_x, self.start_y = None, None
                 return

            abs_x1, abs_y1, abs_x2, abs_y2 = int(x1), int(y1), int(x2), int(y2)
            target_x1, target_y1, target_x2, target_y2 = self.target_region
            final_x1 = max(abs_x1, target_x1)
            final_y1 = max(abs_y1, target_y1)
            final_x2 = min(abs_x2, target_x2)
            final_y2 = min(abs_y2, target_y2)
            width = final_x2 - final_x1
            height = final_y2 - final_y1

            if width < 1 or height < 1:
                 if self.current_annotation_rect_id: self.canvas.delete(self.current_annotation_rect_id)
                 self.status_label.config(text="Durum: İşaretleme hedef bölge dışında veya çok küçük.")
                 self.current_annotation_rect_id = None
                 self.start_x, self.start_y = None, None
                 return

            self.root.attributes('-alpha', 0.0)
            self.root.update()
            time.sleep(0.1)

            annotation_saved = False
            label_written = False
            annotation_file_path = ""
            label_file_path = ""
            yolo_line = ""
            saved_canvas_id = self.current_annotation_rect_id # ID'yi sakla

            try:
                # 1. Kaydet
                screenshot = pyautogui.screenshot(region=(final_x1, final_y1, width, height))
                annotation_file_name = self.generate_filename(self.annotation_subfolder_path, 3, ".jpg")
                annotation_file_path = os.path.join(self.annotation_subfolder_path, annotation_file_name)
                screenshot.save(annotation_file_path)
                annotation_saved = True

                # 2. Hesapla
                target_width = target_x2 - target_x1
                target_height = target_y2 - target_y1
                box_width = final_x2 - final_x1
                box_height = final_y2 - final_y1
                box_center_x_abs = final_x1 + box_width / 2
                box_center_y_abs = final_y1 + box_height / 2
                box_center_x_rel = box_center_x_abs - target_x1
                box_center_y_rel = box_center_y_abs - target_y1
                x_center_norm = max(0.0, min(1.0, box_center_x_rel / target_width))
                y_center_norm = max(0.0, min(1.0, box_center_y_rel / target_height))
                width_norm = max(0.0, min(1.0, box_width / target_width))
                height_norm = max(0.0, min(1.0, box_height / target_height))

                # 3. Yaz
                class_name = self.annotation_subfolder
                label_file_path = os.path.join(self.labels_folder, f"{self.current_target_basename}.txt")
                yolo_line = f"{class_name} {x_center_norm:.6f} {y_center_norm:.6f} {width_norm:.6f} {height_norm:.6f}\n"
                with open(label_file_path, 'a', encoding='utf-8') as f: f.write(yolo_line)
                label_written = True

                # Başarılıysa canvas'taki dikdörtgeni kalıcı yap (width=2)
                self.canvas.itemconfig(saved_canvas_id, outline='green', width=2) # Kaydedileni biraz daha ince yap
                self.annotation_rects_ids.append(saved_canvas_id) # Kalıcı listeye ekle

                # Geri alma için bilgileri sakla
                self.last_annotation_details = {
                    'img_path': annotation_file_path,
                    'lbl_path': label_file_path,
                    'lbl_line': yolo_line, # Satır sonu karakteri dahil
                    'canvas_id': saved_canvas_id
                }
                self.status_label.config(text=f"Kaydedildi: ...{os.path.basename(annotation_file_path)} | Etiket eklendi: {os.path.basename(label_file_path)} ('Z' ile Geri Al)")

            except Exception as e:
                error_msg = f"İşaretleme kaydedilirken/etiketlenirken hata: {str(e)}"
                if annotation_saved and not label_written: error_msg += f"\nResim kaydedildi ({annotation_file_path}) ancak etiket dosyası yazılamadı!"
                elif not annotation_saved: error_msg += f"\nResim kaydedilemedi ({annotation_file_path})."
                messagebox.showerror("Hata", error_msg)
                # Hata durumunda geçici dikdörtgeni sil
                if saved_canvas_id and saved_canvas_id not in self.annotation_rects_ids:
                    self.canvas.delete(saved_canvas_id)
                # Geri alma bilgilerini temizle
                self.last_annotation_details = None
            finally:
                 self.root.attributes('-alpha', 0.3)
                 self.current_annotation_rect_id = None # İşlem bitti, geçici ID'yi sıfırla
                 self.start_x, self.start_y = None, None

    # ----- Geri Alma Fonksiyonu -----
    def undo_last_annotation(self, event=None):
        """Son yapılan işaretlemeyi geri alır."""
        if self.mode != 'annotating':
            self.status_label.config(text="Durum: Geri alma işlemi sadece işaretleme modunda yapılabilir.")
            return

        if not self.last_annotation_details:
            self.status_label.config(text="Durum: Geri alınacak son işaretleme bulunamadı.")
            return

        details = self.last_annotation_details
        img_path = details['img_path']
        lbl_path = details['lbl_path']
        lbl_line_to_remove = details['lbl_line'] # Satır sonu dahil olmalı
        canvas_id = details['canvas_id']

        # 1. Canvas'tan dikdörtgeni sil
        try:
            # ID'nin hala listede olup olmadığını kontrol et (ekstra güvenlik)
            if canvas_id in self.annotation_rects_ids:
                self.canvas.delete(canvas_id)
                self.annotation_rects_ids.remove(canvas_id)
            else:
                # Belki zaten silinmiş veya bir tutarsızlık var
                 print(f"Uyarı: Geri alınmak istenen canvas öğesi (ID: {canvas_id}) listede bulunamadı.")
                 pass # Yine de devam etmeyi dene
        except tk.TclError as e:
             print(f"Canvas öğesi silinirken hata (ID: {canvas_id}): {e}")
             # Öğe zaten yoksa devam et

        # 2. Etiket dosyasından ilgili satırı sil
        lines_kept = []
        line_removed = False
        try:
            if os.path.exists(lbl_path):
                with open(lbl_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                # Sondan başlayarak eşleşen ilk satırı atla (en son eklenen)
                # VEYA daha basit: son satırı silmeyi dene (eğer bu son işlemse)
                if lines and lines[-1] == lbl_line_to_remove:
                     lines.pop() # Son satırı sil
                     line_removed = True
                else:
                     # Eğer son satır eşleşmiyorsa, belki manuel editlendi.
                     # Bu durumda işlem yapmamak daha güvenli olabilir veya
                     # tüm satırlarda arayıp son eşleşeni bulup silmek gerekir (daha karmaşık).
                     # Şimdilik sadece son satır eşleşirse silelim.
                     print(f"Uyarı: Etiket dosyasındaki ({lbl_path}) son satır geri alınmak istenenle ({lbl_line_to_remove.strip()}) eşleşmiyor.")

                if line_removed:
                    with open(lbl_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
            else:
                 print(f"Uyarı: Etiket dosyası ({lbl_path}) bulunamadı.")

        except Exception as e:
            messagebox.showerror("Hata", f"Etiket dosyası güncellenirken hata: {e}")
            # Etiket güncellenemese bile devam et, resmi silmeyi dene

        # 3. İşaretleme resmini sil
        img_deleted = False
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
                img_deleted = True
            else:
                print(f"Uyarı: İşaretleme resmi ({img_path}) bulunamadı.")
        except Exception as e:
            messagebox.showerror("Hata", f"İşaretleme resmi silinirken hata: {e}")

        # Başarı durumunu güncelle ve geri alma bilgisini temizle
        if line_removed or img_deleted: # En az bir işlem yapıldıysa
            self.status_label.config(text="Durum: Son işaretleme geri alındı.")
        else:
            # Hiçbir şey yapılamadıysa (dosyalar yok vb.)
             self.status_label.config(text="Durum: Geri alma işlemi sırasında dosya bulunamadı veya hata oluştu.")

        # Geri alma bilgisini temizle ki tekrar aynı şeyi geri almasın
        self.last_annotation_details = None


    # ----- Yardımcı Fonksiyonlar -----
    def generate_filename(self, folder_path, num_digits, extension=".jpg"):
        os.makedirs(folder_path, exist_ok=True)
        files = os.listdir(folder_path)
        pattern = f"{{:0{num_digits}d}}{extension}"
        numeric_files = [f for f in files if f.endswith(extension) and len(f) == num_digits + len(extension) and f[:num_digits].isdigit()]
        if not numeric_files: next_number = 1
        else:
            highest = 0
            for f in numeric_files:
                try: highest = max(highest, int(f[:num_digits]))
                except ValueError: pass
            next_number = highest + 1
        return pattern.format(next_number)

    def exit_program(self, event=None):
        self.root.destroy()


if __name__ == "__main__":
    try:
        import tkinter
        import pyautogui
        from PIL import Image, ImageTk
        import time
        from tkinter import simpledialog
    except ImportError as e:
        print(f"Gerekli kütüphane eksik: {e}")
        print("Lütfen 'pip install pillow pyautogui' komutunu çalıştırın.")
        exit(1)

    root = tk.Tk()
    app = ScreenCapture(root)
    root.mainloop()