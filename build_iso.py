import os
import sys
import pycdlib

def create_burgood_iso():
    source_dir = r"D:\BurgoodAccsesCantrol\iso_staging"
    iso_path = r"D:\BurgoodAccsesCantrol\BurgoodAccessControl.iso"
    
    print(f"UDF ISO yaratilmoqda: {iso_path}")
    if os.path.exists(iso_path):
        try:
            os.remove(iso_path)
        except Exception:
            pass

    # Nusxalash
    exe_src = r"D:\BurgoodAccsesCantrol\dist\BurgoodAccessControl.exe"
    if os.path.exists(exe_src):
        import shutil
        shutil.copy2(exe_src, os.path.join(source_dir, "BurgoodAccessControl.exe"))

    # Autorun va yo'riqnoma tayyorlash
    autorun_path = os.path.join(source_dir, "autorun.inf")
    with open(autorun_path, "w", encoding="utf-8") as f:
        f.write("[autorun]\nopen=O'rnatish.bat\nicon=BurgoodAccessControl.exe,0\nlabel=Burgood Access Control\n")

    info_path = os.path.join(source_dir, "Yo'riqnoma.txt")
    with open(info_path, "w", encoding="utf-8") as f:
        f.write("BURGOOD ACCESS CONTROL - FACE ID & DAVOMAT TIZIMI\n")
        f.write("===================================================\n\n")
        f.write("Dasturni o'rnatish va ishga tushirish uchun 'O'rnatish.bat' faylini 2 marta bosing.\n")
        f.write("U avtomatik tarzda Ish stolingizga (Desktop) chiroyli yorliq chiqaradi.\n\n")
        f.write("Texnik yordam: @BurgoodAccsesCantrolMaster_bot\n")

    iso = pycdlib.PyCdlib()
    iso.new(udf='2.60', vol_ident="BURGOOD_AC")

    dirs_created = set()

    for root, dirs, files in os.walk(source_dir):
        rel_root = os.path.relpath(root, source_dir)
        if rel_root != ".":
            parts = rel_root.replace("\\", "/").strip("/").split("/")
            curr_dir = ""
            for p in parts:
                curr_dir += "/" + p
                if curr_dir not in dirs_created:
                    try:
                        iso.add_directory(udf_path=curr_dir)
                    except Exception as e:
                        pass
                    dirs_created.add(curr_dir)

        for f in files:
            full_f_path = os.path.join(root, f)
            rel_f = os.path.relpath(full_f_path, source_dir).replace("\\", "/")
            udf_f_path = "/" + rel_f.lstrip("/")

            try:
                iso.add_file(full_f_path, udf_path=udf_f_path)
            except Exception as e:
                print(f"Xato: {udf_f_path}: {e}")

    print("ISO disk fayli yozilmoqda, kuting...")
    iso.write(iso_path)
    iso.close()
    
    size_mb = os.path.getsize(iso_path) / (1024 * 1024)
    print(f"MUVAFFAQIYAT! BurgoodAccessControl.iso to'liq yaratildi: {size_mb:.2f} MB")

if __name__ == "__main__":
    create_burgood_iso()
