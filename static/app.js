function babyMachine() {
    return {
        ledButtons: [
            { id: 'led1', label: 'Red', color: 'red-600', emoji: '🔆', state: false },
            { id: 'led2', label: 'Yellow', color: 'yellow-600', emoji: '🔆', state: false }
        ],
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
                this.ledButtons.forEach(led => {
                    led.state = data[led.id] || false;
                });
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
                    const led = this.ledButtons.find(l => l.id === ledId);
                    if (led) {
                        led.state = data.state;
                    }
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
