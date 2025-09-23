        // Auto-focus for printing
        window.onload = function() {
            // Auto print after 2 seconds if opened in new window
            setTimeout(function() {
                if (window.opener) {
                    window.print();
                }
            }, 1000);
        };

        // Close window after printing
        window.onafterprint = function() {
            if (window.opener) {
                setTimeout(function() {
                    window.close();
                }, 1000);
            }
        };
