// Barcode scanner using html5-qrcode library

class BarcodeScanner {
  constructor(containerId, onScan) {
    this.containerId = containerId;
    this.onScan = onScan;
    this.scanner = null;
    this.isScanning = false;
    this.isStarting = false;
  }

  /**
   * Clean up scanner instance completely.
   * Stops camera stream and removes DOM elements.
   */
  async cleanup() {
    if (!this.scanner) return;

    try {
      if (this.isScanning) {
        await this.scanner.stop();
      }
    } catch (e) {
      // Ignore stop errors
    }

    try {
      await this.scanner.clear();
    } catch (e) {
      // Ignore clear errors
    }

    this.scanner = null;
    this.isScanning = false;
  }

  async start() {
    // Don't start if already scanning or currently starting (prevents duplicate cameras)
    if (this.isScanning || this.isStarting) return;
    this.isStarting = true;

    try {
      // Clean up any previous instance first
      await this.cleanup();

      const { Html5Qrcode } = window;

      const scanConfig = {
        fps: 10,
        qrbox: { width: 250, height: 150 },
        aspectRatio: 1.5,
      };

      const onSuccess = (decodedText) => {
        if (this.isValidISBN(decodedText)) {
          this.onScan(decodedText);
          this.stop();
        }
      };

      const onError = () => {
        // Ignore scan errors (they happen continuously until a code is found)
      };

      // Create fresh scanner instance
      this.scanner = new Html5Qrcode(this.containerId);

      try {
        // Try back camera first (preferred for scanning)
        await this.scanner.start(
          { facingMode: 'environment' },
          scanConfig,
          onSuccess,
          onError
        );
        this.isScanning = true;
      } catch (err) {
        console.error('Back camera failed, trying front camera:', err);

        // Clean up failed attempt completely
        await this.cleanup();

        // Create fresh instance for retry
        this.scanner = new Html5Qrcode(this.containerId);

        try {
          await this.scanner.start(
            { facingMode: 'user' },
            scanConfig,
            onSuccess,
            onError
          );
          this.isScanning = true;
        } catch (err2) {
          console.error('All camera attempts failed:', err2);
          await this.cleanup();
          throw new Error('Could not access camera. Please allow camera permissions and ensure you\'re on HTTPS.');
        }
      }
    } finally {
      this.isStarting = false;
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
