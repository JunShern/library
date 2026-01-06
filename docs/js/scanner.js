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

    const scanConfig = {
      fps: 10,
      qrbox: { width: 250, height: 150 },
      aspectRatio: 1.5,
    };

    const onSuccess = (decodedText) => {
      // ISBN barcodes are typically EAN-13 or ISBN-10/13
      if (this.isValidISBN(decodedText)) {
        this.onScan(decodedText);
        this.stop();
      }
    };

    const onError = () => {
      // Ignore scan errors (they happen continuously until a code is found)
    };

    // Always create a fresh scanner instance to avoid state issues
    this.scanner = new Html5Qrcode(this.containerId);

    try {
      // Try back camera first
      await this.scanner.start(
        { facingMode: 'environment' },
        scanConfig,
        onSuccess,
        onError
      );
      this.isScanning = true;
    } catch (err) {
      console.error('Back camera failed, trying fallback:', err);

      // Clear the failed scanner and create a fresh one
      try {
        await this.scanner.clear();
      } catch (e) {
        // Ignore clear errors
      }
      this.scanner = new Html5Qrcode(this.containerId);

      try {
        // Fallback: try front camera
        await this.scanner.start(
          { facingMode: 'user' },
          scanConfig,
          onSuccess,
          onError
        );
        this.isScanning = true;
      } catch (err2) {
        console.error('All camera attempts failed:', err2);
        throw new Error('Could not access camera. Please allow camera permissions and ensure you\'re on HTTPS.');
      }
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
