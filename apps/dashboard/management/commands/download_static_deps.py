# yourapp/management/commands/download_static_deps.py
import os
import requests
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
import zipfile
from io import BytesIO

class Command(BaseCommand):
    help = 'Downloads required static dependencies'

    DEPENDENCIES = {
        'js': {
            'jquery': 'https://code.jquery.com/jquery-3.7.1.min.js',
            'select2': 'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
            'toastr': 'https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.js',
            'htmx': 'https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js',
        },
        'css': {
            'select2': 'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
            'toastr': 'https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.css',
        },
        'packages': {
            'bootstrap-icons': {
                'url': 'https://github.com/twbs/icons/releases/download/v1.11.3/bootstrap-icons-1.11.3.zip',
                'css_path': 'bootstrap-icons.css',
                'fonts_path': 'fonts/*'
            }
        }
    }

    def handle(self, *args, **kwargs):
        static_root = os.path.join(settings.BASE_DIR, 'static')
        
        # Create directories if they don't exist
        for dir_name in ['js', 'css', 'webfonts']:
            os.makedirs(os.path.join(static_root, dir_name), exist_ok=True)

        # Download JS files
        for name, url in self.DEPENDENCIES['js'].items():
            filepath = os.path.join(static_root, 'js', f'{name}.min.js')
            self.download_file(url, filepath)

        # Download CSS files
        for name, url in self.DEPENDENCIES['css'].items():
            filepath = os.path.join(static_root, 'css', f'{name}.min.css')
            self.download_file(url, filepath)

        # Download and extract packages
        for name, package_info in self.DEPENDENCIES['packages'].items():
            self.handle_package(name, package_info, static_root)

    def download_file(self, url, filepath):
        self.stdout.write(f'Downloading {url}...')
        response = requests.get(url)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            self.stdout.write(self.style.SUCCESS(f'Successfully downloaded to {filepath}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to download {url}'))

    def handle_package(self, name, package_info, static_root):
        self.stdout.write(f'Downloading and extracting {name}...')
        
        # Download the zip file
        response = requests.get(package_info['url'])
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f'Failed to download {name}'))
            return

        # Extract the zip file
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            # Extract CSS
            css_file = package_info.get('css_path')
            if css_file:
                try:
                    z.extract(css_file, os.path.join(static_root, 'css'))
                    # Move the file to the correct location if it's in a subdirectory
                    extracted_path = os.path.join(static_root, 'css', css_file)
                    final_path = os.path.join(static_root, 'css', 'bootstrap-icons.css')
                    os.rename(extracted_path, final_path)
                except KeyError:
                    self.stdout.write(self.style.WARNING(f'CSS file {css_file} not found in package'))

            # Extract fonts
            fonts_path = package_info.get('fonts_path')
            if fonts_path:
                font_files = [f for f in z.namelist() if f.startswith('fonts/')]
                for font_file in font_files:
                    try:
                        z.extract(font_file, os.path.join(static_root, 'webfonts'))
                    except KeyError:
                        self.stdout.write(self.style.WARNING(f'Font file {font_file} not found in package'))

        self.stdout.write(self.style.SUCCESS(f'Successfully extracted {name}'))