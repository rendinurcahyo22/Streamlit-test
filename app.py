import streamlit as st
import streamlit.components.v1 as components
import base64
import io
from PIL import Image

# HTML dan JavaScript untuk mengambil tangkapan layar dari sisi klien (browser pengguna)
# Menggunakan html2canvas untuk menangkap seluruh halaman Streamlit yang bisa di-scroll.
CLIENT_SIDE_SCREEN_CAPTURE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Streamlit Page Capture</title>
    <!-- Streamlit Component Library -->
    <script src="https://unpkg.com/streamlit-component-lib/dist/streamlit-component-lib.js"></script>
    <!-- html2canvas library -->
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <style>
      /* --- CSS Reset Minimalis dan Styling Komponen --- */
      html, body {
        margin: 0;
        padding: 0;
        line-height: 1.5; /* Default line-height yang baik */
        letter-spacing: normal; /* Pastikan normal */
        font-family: 'Inter', sans-serif;
      }
      body {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        min-height: 200px;
        padding: 20px;
        background-color: #f0f2f6;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        width: 100%;
        box-sizing: border-box;
      }
      /* Paksa line-height dan letter-spacing untuk elemen teks */
      p, h1, h2, h3, h4, h5, h6, li {
        line-height: 1.5 !important;
        letter-spacing: normal !important;
        word-break: break-word; /* Mencegah kata terlalu panjang merusak layout */
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
  <p>Tekan tombol di bawah ini untuk menangkap tampilan halaman Streamlit ini.</p>
  <div class="button-container">
      <button id="captureButton">Tangkap Halaman Penuh (PNG)</button>
  </div>
  <p id="status-message"></p>
  <img id="preview-img" alt="Pratinjau Tangkapan Halaman">

<script>
  window.onload = function() {
    console.log("[JS] Window onload event fired. DOM fully loaded.");
    const captureButton = document.getElementById('captureButton');
    const statusMessage = document.getElementById('status-message');
    const previewImg = document.getElementById('preview-img');

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
      updateStatus("Sedang menangkap halaman penuh... Mohon tunggu sebentar. ⏳");
      previewImg.style.display = 'none';

      try {
        if (typeof window.html2canvas === 'undefined') {
            updateStatus("Error: html2canvas library tidak ditemukan. 😞", 'error');
            console.error("[JS Error] html2canvas is not defined. CDN might not have loaded.");
            sendValueToStreamlit(null);
            return;
        }

        // --- Peningkatan Opsi html2canvas untuk Kualitas Rendering & Full Page ---
        const targetElement = window.parent.document.body;
        const scrollWidth = Math.max(
          targetElement.scrollWidth,
          targetElement.offsetWidth,
          targetElement.clientWidth,
          window.parent.document.documentElement.scrollWidth,
          window.parent.document.documentElement.offsetWidth,
          window.parent.document.documentElement.clientWidth
        );
        const scrollHeight = Math.max(
          targetElement.scrollHeight,
          targetElement.offsetHeight,
          targetElement.clientHeight,
          window.parent.document.documentElement.scrollHeight,
          window.parent.document.documentElement.offsetHeight,
          window.parent.document.documentElement.clientHeight
        );

        const canvas = await window.html2canvas(targetElement, {
            scale: 4, // Meningkatkan skala rendering untuk ketajaman yang lebih baik
            logging: true, // Aktifkan logging untuk debug di konsol browser
            useCORS: true, // Penting untuk memuat gambar lintas domain
            backgroundColor: '#ffffff', // Tentukan warna latar belakang eksplisit
            windowWidth: scrollWidth, // Set lebar window untuk capture seluruh halaman
            windowHeight: scrollHeight, // Set tinggi window untuk capture seluruh halaman
            scrollX: 0, // Mulai capture dari scroll 0
            scrollY: 0, // Mulai capture dari scroll 0
            foreignObjectRendering: true, // Coba gunakan rendering foreignObject untuk akurasi yang lebih baik
            ignoreElements: (element) => element.tagName === 'IFRAME' && element.src.includes('streamlit-custom-component')
        });

        const imageDataUrl = canvas.toDataURL('image/png');

        previewImg.src = imageDataUrl;
        previewImg.style.display = 'block';

        updateStatus("Halaman berhasil ditangkap sebagai gambar! Mengirim data ke Streamlit. ✨", 'success');
        sendValueToStreamlit(imageDataUrl);
      } catch (err) {
          updateStatus(`Terjadi kesalahan saat menangkap halaman: ${err.message} 😞`, 'error');
          console.error("[JS Error] Error during html2canvas capture:", err);
          sendValueToStreamlit(null);
      }
    };

    if (window.parent && window.parent.Streamlit) {
        window.parent.Streamlit.setComponentReady();
        window.parent.Streamlit.setFrameHeight(document.body.scrollHeight);
        updateStatus("Komponen siap! Tekan tombol untuk menangkap halaman. ✅", 'info');
    } else {
        console.warn("[JS Warning] Streamlit parent tidak tersedia saat setComponentReady dipanggil. Mungkin ada masalah inisialisasi.");
        updateStatus("Error inisialisasi Streamlit. Coba muat ulang halaman. �", 'error');
    }
  }; // End window.onload
</script>
</body>
</html>
"""

st.set_page_config(page_title="Tangkap Halaman Streamlit ke Gambar", layout="centered")

st.title("📸 Tangkap Halaman Streamlit Ini")
st.markdown("""
Aplikasi ini memungkinkan Anda mengambil tangkapan gambar dari **seluruh halaman Streamlit ini** yang sedang Anda lihat di browser, termasuk bagian yang perlu di-scroll.

**Penting:**
* Ini akan menangkap seluruh konten halaman Streamlit, bahkan jika Anda perlu menggulirnya.
* Kualitas *rendering* (font, spasi) mungkin tidak 100% sempurna seperti *screenshot* bawaan sistem operasi karena menggunakan *library* JavaScript untuk menggambar ulang HTML.
* Ketika Anda mengunduh gambar di ponsel, perilaku penyimpanannya (misalnya, langsung ke galeri atau ke folder "Downloads") akan tergantung pada browser dan sistem operasi ponsel Anda.
""")

# Menampilkan komponen HTML/JavaScript
captured_data_url = components.html(
    CLIENT_SIDE_SCREEN_CAPTURE_HTML,
    height=550,
    scrolling=False
)

# Jika data tangkapan layar diterima dari komponen JavaScript
if isinstance(captured_data_url, str):
    st.subheader("Hasil Tangkapan Halaman (Gambar PNG):")
    try:
        if captured_data_url.startswith("data:image/png;base64,"):
            encoded_data = captured_data_url.split(",", 1)[1]
            image_bytes = base64.b64decode(encoded_data)

            st.image(image_bytes, caption="Tangkapan Halaman Streamlit Anda (PNG)", use_column_width=True)
            st.download_button(
                label="💾 Unduh Gambar PNG",
                data=image_bytes,
                file_name="tangkapan_halaman_streamlit.png",
                mime="image/png"
            )
            st.success("Tangkapan halaman sebagai gambar PNG berhasil diterima dan ditampilkan! ✨")
        else:
            st.error("Terjadi kesalahan: Format Data URL gambar tidak valid. Data yang diterima bukan gambar PNG Base64.")
            st.write(f"Data yang diterima (awal): {captured_data_url[:100]}...")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses gambar yang diterima: {e} 😞")
elif captured_data_url is None:
    st.warning("Tangkapan halaman dibatalkan atau tidak ada gambar yang diambil.")
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
2.  Simpan kode di atas sebagai file Python (misalnya, `app_capture_image.py`).
3.  Jalankan dari terminal Anda:
    ```bash
    streamlit run app_capture_image.py
    ```
4.  Buka URL yang diberikan Streamlit di browser Anda (termasuk di ponsel Anda!).
""")