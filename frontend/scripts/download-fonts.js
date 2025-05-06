import fs from 'fs';
import path from 'path';
import https from 'https';
import { fileURLToPath } from 'url';

// Get current directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Create fonts directory if it doesn't exist
const fontsDir = path.join(__dirname, '../public/fonts');
if (!fs.existsSync(fontsDir)) {
  fs.mkdirSync(fontsDir, { recursive: true });
}

// Font files to download
const fonts = [
  {
    name: 'Inter-Regular.woff2',
    url: 'https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.woff2'
  },
  {
    name: 'Inter-Medium.woff2',
    url: 'https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Medium.woff2'
  },
  {
    name: 'Inter-SemiBold.woff2',
    url: 'https://github.com/rsms/inter/raw/master/docs/font-files/Inter-SemiBold.woff2'
  },
  {
    name: 'Inter-Bold.woff2',
    url: 'https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.woff2'
  }
];

// Download each font file
fonts.forEach(font => {
  const filePath = path.join(fontsDir, font.name);
  console.log(`Downloading ${font.name}...`);
  
  const file = fs.createWriteStream(filePath);
  https.get(font.url, response => {
    response.pipe(file);
    file.on('finish', () => {
      file.close();
      console.log(`Downloaded ${font.name} successfully`);
    });
  }).on('error', err => {
    fs.unlink(filePath);
    console.error(`Error downloading ${font.name}: ${err.message}`);
  });
});