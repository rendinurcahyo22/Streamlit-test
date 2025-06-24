import streamlit as st
import streamlit.components.v1 as components
import base64
import io
from PIL import Image

# HTML dan JavaScript untuk mengambil tangkapan layar dari sisi klien (browser pengguna)
# Menggunakan navigator.mediaDevices.getDisplayMedia() untuk akses piksel.
CLIENT_SIDE_SCREEN_CAPTURE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Streamlit Screen Capture</title>
    <!-- Streamlit Component Library -->
    <script src="https://unpkg.com/streamlit-component-lib/dist/streamlit-component-lib.js"></script>
    <style>
      body {
        font-family: 'Inter', sans-serif;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        min-height: 200px;
        padding: 20px;
        background-color: #f0f2f6;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin: 0; 
        width: 100%;
        box-sizing: border-box;
      }
      button {
        background-color: #4CAF50; /* Hijau */
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        transition: background-color 0.3s ease, transform 0.2s ease;
        box-shadow: 0 4px #999;
      }
      button:hover { background-color: #45a049; }
      button:active {
        background-color: #3e8e41;
        box-shadow: 0 2px #666;
        transform: translateY(2px);
      }
      #status-message {
          margin-top: 15px;
          font-size: 0.9em;
          color: #333;
          text-align: center;
          min-height: 20px;
      }
      #preview-img {
          max-width: 100%;
          height: auto;
          margin-top: 20px;
          border: 1px solid #ddd;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.08);
          display: none;
      }
      .button-container {
          display: flex;
          gap: 10px;
          margin-top: 20px;
      }
    </style>
</head>
<body>
  <p>Tekan tombol di bawah ini untuk menangkap layar perangkat Anda.</p>
  <div class="button-container">
      <button id="captureButton">Tangkap Layar (Membutuhkan Akses)</button>
  </div>
  <p id="status-message"></p>
  <img id="preview-img" alt="Pratinjau Tangkapan Layar">

<script>
  window.onload = function() {
    console.log("[JS] Window onload event fired. DOM fully loaded.");
    const captureButton = document.getElementById('captureButton');
    const statusMessage = document.getElementById('status-message');
    const previewImg = document.getElementById('preview-img');
    let mediaStream = null; // Variabel untuk menyimpan media stream

    function updateStatus(message, type = 'info') {
        statusMessage.style.color = type === 'error' ? 'red' : (type === 'success' ? 'green' : '#333');
        statusMessage.innerText = message;
        console.log(`[JS Status] ${message}`);
        if (window.parent && window.parent.Streamlit) {
            window.parent.Streamlit.setFrameHeight(document.body.scrollHeight);
        }
    }

    function sendValueToStreamlit(value) {
        if (window.parent && window.parent.Streamlit) {
            try {
                window.parent.Streamlit.setComponentValue(value);
                console.log("[JS] Data berhasil dikirim ke Streamlit.");
            } catch (e) {
                console.error("[JS Error] Gagal memanggil setComponentValue:", e);
                updateStatus(`Error: Gagal mengirim data ke Streamlit: ${e.message}`, 'error');
            }
        } else {
            console.error("[JS Error] Objek Streamlit parent tidak ditemukan. Tidak dapat mengirim data kembali.");
            updateStatus("Error: Objek Streamlit parent tidak ditemukan. Tidak dapat mengirim data kembali.", 'error');
        }
    }

    captureButton.onclick = async () => {
      updateStatus("Meminta izin tangkap layar... Harap izinkan di pop-up browser. ⏳");
      previewImg.style.display = 'none'; // Sembunyikan pratinjau sebelumnya

      // Hentikan stream sebelumnya jika masih aktif
      if (mediaStream) {
          mediaStream.getTracks().forEach(track => track.stop());
          mediaStream = null;
      }

      try {
        // Meminta izin tangkapan layar dari browser menggunakan getDisplayMedia
        mediaStream = await navigator.mediaDevices.getDisplayMedia({
          video: {
            cursor: "always", // Tampilkan kursor
            displaySurface: "monitor", // 'monitor' untuk seluruh layar, 'window' untuk jendela, 'browser' untuk tab saat ini
          },
          audio: false // Tidak perlu audio
        });

        updateStatus("Menganalisis stream layar... ✅");

        // Buat elemen video untuk memegang stream
        const video = document.createElement('video');
        video.srcObject = mediaStream;
        video.play();

        // Ketika metadata video sudah dimuat, kita bisa menggambar frame-nya
        video.onloadedmetadata = () => {
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const context = canvas.getContext('2d');

          // Gambar frame video ke elemen canvas
          context.drawImage(video, 0, 0, canvas.width, canvas.height);

          // Ubah konten canvas menjadi Data URL (Base64 encoded PNG)
          const imageDataUrl = canvas.toDataURL('image/png');

          // Hentikan media stream setelah frame ditangkap
          mediaStream.getTracks().forEach(track => track.stop());
          mediaStream = null; // Bersihkan objek stream

          // Tampilkan pratinjau gambar di dalam komponen HTML itu sendiri
          previewImg.src = imageDataUrl;
          previewImg.style.display = 'block';

          updateStatus("Tangkapan layar berhasil! Data dikirim ke Streamlit. ✨", 'success');
          sendValueToStreamlit(imageDataUrl);

        };

      } catch (err) {
          // Tangani jika pengguna membatalkan atau terjadi kesalahan
          if (err.name === "NotAllowedError") {
              updateStatus("Tangkapan layar dibatalkan atau izin tidak diberikan oleh pengguna. 🚫", 'error');
          } else {
              updateStatus(`Terjadi kesalahan: ${err.message} 😞`, 'error');
          }
          if (mediaStream) { // Pastikan stream dihentikan juga saat terjadi error
              mediaStream.getTracks().forEach(track => track.stop());
              mediaStream = null;
          }
          sendValueToStreamlit(null); // Kirim null kembali ke Streamlit untuk mengindikasikan kegagalan
      }
    };

    if (window.parent && window.parent.Streamlit) {
        window.parent.Streamlit.setComponentReady();
        window.parent.Streamlit.setFrameHeight(document.body.scrollHeight);
        updateStatus("Komponen siap! Tekan tombol untuk menangkap layar. ✅", 'info');
    } else {
        console.warn("[JS Warning] Streamlit parent tidak tersedia saat setComponentReady dipanggil. Mungkin ada masalah inisialisasi.");
        updateStatus("Error inisialisasi Streamlit. Coba muat ulang halaman. 😞", 'error');
    }
  }; // End window.onload
</script>
</body>
</html>
"""

st.set_page_config(page_title="Tangkap Layar Perangkat (Akses Dibutuhkan)", layout="centered")

st.title("📸 Tangkap Layar Perangkat Ini")
st.markdown("""
Aplikasi ini memungkinkan Anda mengambil tangkapan gambar dari **layar perangkat Anda** yang sedang Anda gunakan.

**Penting:**
* Ini akan memicu *pop-up* izin browser untuk berbagi layar. Anda harus **mengizinkan dan memilih** area yang ingin ditangkap (seluruh layar, jendela aplikasi, atau tab browser).
* Tangkapan yang dihasilkan adalah *screenshot* piksel dari area yang Anda pilih.
* Ketika Anda mengunduh gambar di ponsel, perilaku penyimpanannya (misalnya, langsung ke galeri atau ke folder "Downloads") akan tergantung pada browser dan sistem operasi ponsel Anda.
""")

# Menampilkan komponen HTML/JavaScript
captured_data_url = components.html(
    CLIENT_SIDE_SCREEN_CAPTURE_HTML,
    height=550, # Ditingkatkan agar tombol, pesan, dan pratinjau muat
    scrolling=False
)

# Jika data tangkapan layar diterima dari komponen JavaScript
if isinstance(captured_data_url, str):
    st.subheader("Hasil Tangkapan Layar Anda (Gambar PNG):")
    try:
        if captured_data_url.startswith("data:image/png;base64,"):
            encoded_data = captured_data_url.split(",", 1)[1]
            image_bytes = base64.b64decode(encoded_data)

            st.image(image_bytes, caption="Tangkapan Layar Perangkat Anda", use_column_width=True)
            st.download_button(
                label="💾 Unduh Gambar PNG",
                data=image_bytes,
                file_name="tangkapan_layar_perangkat.png",
                mime="image/png"
            )
            st.success("Tangkapan layar berhasil diterima dan ditampilkan! ✨")
        else:
            st.error("Terjadi kesalahan: Format Data URL gambar tidak valid. Data yang diterima bukan gambar PNG Base64.")
            st.write(f"Data yang diterima (awal): {captured_data_url[:100]}...")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses gambar yang diterima: {e} 😞")
elif captured_data_url is None:
    st.warning("Tangkapan layar dibatalkan atau tidak ada gambar yang diambil.")
else:
    st.error(f"Terjadi kesalahan: Tipe data yang diterima dari komponen tidak sesuai (tipe: {type(captured_data_url)}). 😞")
    st.write(f"Nilai yang diterima: {captured_data_url}")


st.markdown("""
---
**Cara Menjalankan Aplikasi Ini:**

1.  Pastikan Anda telah menginstal Streamlit dan Pillow:
    ```bash
    pip install streamlit Pillow
    ```
    (Tidak perlu `mss` atau `html2canvas` library di Python, hanya di frontend HTML).
2.  Simpan kode di atas sebagai file Python (misalnya, `app_capture_screen.py`).
3.  Jalankan dari terminal Anda:
    ```bash
    streamlit run app_capture_screen.py
    ```
4.  Buka URL yang diberikan Streamlit di browser Anda (termasuk di ponsel Anda!).
""")
