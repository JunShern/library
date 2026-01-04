// Barcode scanner using html5-qrcode library

class BarcodeScanner {
  constructor(containerId, onScan) {
    this.containerId = containerId;
    this.onScan = onScan;
    this.scanner = null;
    this.isScanning = false;
  }

  async start() {
    if (this.isScanning) return;

    const { Html5Qrcode } = window;
    this.scanner = new Html5Qrcode(this.containerId);

    try {
      await this.scanner.start(
        { facingMode: 'environment' },
        {
          fps: 10,
          qrbox: { width: 250, height: 150 },
          aspectRatio: 1.5,
        },
        (decodedText) => {
          // ISBN barcodes are typically EAN-13 or ISBN-10/13
          if (this.isValidISBN(decodedText)) {
            this.onScan(decodedText);
            this.stop();
          }
        },
        (errorMessage) => {
          // Ignore scan errors (they happen continuously until a code is found)
        }
      );
      this.isScanning = true;
    } catch (err) {
      console.error('Scanner start error:', err);
      throw new Error('Could not access camera. Please allow camera permissions.');
    }
  }

  async stop() {
    if (this.scanner && this.isScanning) {
      try {
        await this.scanner.stop();
        this.isScanning = false;
      } catch (err) {
        console.error('Scanner stop error:', err);
      }
    }
  }

  isValidISBN(code) {
    // Remove any hyphens or spaces
    const cleaned = code.replace(/[-\s]/g, '');

    // ISBN-10: 10 digits (last can be X)
    if (/^\d{9}[\dX]$/.test(cleaned)) {
      return true;
    }

    // ISBN-13: 13 digits, starts with 978 or 979
    if (/^97[89]\d{10}$/.test(cleaned)) {
      return true;
    }

    // EAN-13 (general): 13 digits
    if (/^\d{13}$/.test(cleaned)) {
      return true;
    }

    return false;
  }

  normalizeISBN(code) {
    return code.replace(/[-\s]/g, '');
  }
}

// Export for use in add-book.html
window.BarcodeScanner = BarcodeScanner;
