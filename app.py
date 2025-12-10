from flask import Flask, render_template, request, send_file, redirect, url_for
import yt_dlp
import os
import base64

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads' 
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form.get('url')
        if not video_url:
            return render_template('index.html', error='សូមបញ្ចូល URL វីដេអូ!')

        # ដំណាក់កាលទី ១: ទាញយកតែព័ត៌មាន (Metadata និង Preview URL)
        ydl_opts_info = {
            'noplaylist': True,
            'quiet': True,
            'skip_download': True,
            'force_generic_extractor': False, 
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                encoded_url = base64.urlsafe_b64encode(video_url.encode()).decode()
                
                video_data = {
                    'title': info.get('title'),
                    'duration': info.get('duration_string'),
                    'encoded_url': encoded_url,
                    'direct_url': info.get('url'), 
                    'thumbnail': info.get('thumbnail')
                }
                
            return render_template('index.html', video_data=video_data)
        
        except Exception as e:
            return render_template('index.html', error=f'មានកំហុសក្នុងការទាញយកព័ត៌មាន: {e}')

    return render_template('index.html')

@app.route('/download_file/<encoded_url>', methods=['POST'])
def download_file(encoded_url):
    # ដំណាក់កាលទី ២: ដំណើរការទាញយកឯកសារពិតប្រាកដ
    try:
        video_url = base64.urlsafe_b64decode(encoded_url.encode()).decode()
    except:
        return redirect(url_for('index', error='URL មិនត្រឹមត្រូវ!'))

    ydl_opts_download = {
        # ដំណោះស្រាយថ្មី៖ ប្រើ best[ext=mp4][vcodec!=none][acodec!=none] ដើម្បីបង្ខំឲ្យមាន MP4 វីដេអូដែលមានសំឡេងរួមបញ្ចូល
        # នេះក៏ជួយដោះស្រាយបញ្ហា ២ ឯកសារ ដោយមិនពឹងផ្អែកលើ FFmpeg
        'format': 'best[ext=mp4][vcodec!=none][acodec!=none]/best', 
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
            info = ydl.extract_info(video_url, download=True)
            # ស្វែងរកឯកសារដែលបានទាញយកដោយ yt-dlp
            file_path = ydl.prepare_filename(info)

            # ជួនកាល file_path ចង្អុលទៅ Folder ជំនួសឲ្យ File មួយ
            # យើងត្រូវស្វែងរកឯកសារ .mp4 តែមួយគត់នៅក្នុង folder downloads
            # នេះគឺជាដំណោះស្រាយបន្ថែម
            downloaded_files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(info.get('id', '')) and f.endswith('.mp4')]
            if downloaded_files:
                final_path = os.path.join(DOWNLOAD_FOLDER, downloaded_files[0])
                return send_file(final_path, as_attachment=True, download_name=os.path.basename(final_path))
            
            # បើរកមិនឃើញ ប្រើ path ដើមវិញ
            return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

    
    except Exception as e:
        return redirect(url_for('index', error=f'មានកំហុសក្នុងការទាញយកឯកសារ: {e}'))

if __name__ == '__main__':
    app.run(debug=True)