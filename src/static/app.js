function babyMachine() {
    return {
        leds: {
            led1: false,
            led2: false,
        },
        volume: 0.5,
        isPlaying: false,

        init() {
            // Load LED states on init
            this.loadLEDStates();
        },

        async loadLEDStates() {
            try {
                const response = await fetch('/led_status');
                const data = await response.json();
                this.leds = data;
            } catch (error) {
                console.error('Failed to load LED states:', error);
            }
        },

        async toggleLED(ledId) {
            try {
                const response = await fetch(`/toggle_led/${ledId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.leds[ledId] = data.state;
                }
            } catch (error) {
                console.error('Failed to toggle LED:', error);
            }
        },

        async startWhiteNoise() {
            try {
                const response = await fetch('/white_noise/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ volume: this.volume })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.isPlaying = true;
                }
            } catch (error) {
                console.error('Failed to start white noise:', error);
            }
        },

        async stopWhiteNoise() {
            try {
                const response = await fetch('/white_noise/stop', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.isPlaying = false;
                }
            } catch (error) {
                console.error('Failed to stop white noise:', error);
            }
        },

        async updateVolume() {
            if (this.isPlaying) {
                try {
                    await fetch('/white_noise/volume', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ volume: this.volume })
                    });
                } catch (error) {
                    console.error('Failed to update volume:', error);
                }
            }
        }
    }
}
