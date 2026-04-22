"""
Noise Reduction Module

This module handles noise reduction processing for audio files.
Uses spectral subtraction and adaptive filtering techniques.
"""
import os
import logging
import numpy as np
import soundfile as sf
from scipy import signal
import librosa


class NoiseReducer:
    """Class for reducing noise in audio recordings."""
    
    def __init__(self, strength=0.3):
        """
        Initialize the noise reducer.
        
        Args:
            strength (float): Noise reduction strength (0.0 to 1.0)
        """
        self.strength = min(max(strength, 0.0), 1.0)  # Clamp between 0 and 1
        logging.info(f"Initializing NoiseReducer with strength={self.strength}")
    
    def _estimate_noise_profile(self, audio_data, sr, frame_length=2048, hop_length=512):
        """
        Estimate noise profile from the audio data.
        Uses the beginning of the file as reference noise.
        
        Args:
            audio_data (np.ndarray): Audio data
            sr (int): Sample rate
            frame_length (int): FFT frame length
            hop_length (int): Hop length for STFT
            
        Returns:
            np.ndarray: Noise profile
        """
        # Use first 1-2 seconds to estimate noise
        noise_sample_duration = min(2.0, len(audio_data) / sr / 10)
        noise_samples = int(noise_sample_duration * sr)
        
        # Get noise profile
        noise_clip = audio_data[:noise_samples]
        
        # Compute STFT of noise
        noise_stft = librosa.stft(noise_clip, n_fft=frame_length, hop_length=hop_length)
        noise_spec = np.abs(noise_stft)
        
        # Estimate noise statistics
        noise_profile = np.mean(noise_spec, axis=1)
        return noise_profile[:, np.newaxis]  # Return as column vector
    
    def _spectral_subtraction(self, audio_data, sr, noise_profile, 
                              frame_length=2048, hop_length=512):
        """
        Perform spectral subtraction to reduce noise.
        
        Args:
            audio_data (np.ndarray): Audio data
            sr (int): Sample rate
            noise_profile (np.ndarray): Noise profile
            frame_length (int): FFT frame length
            hop_length (int): Hop length for STFT
            
        Returns:
            np.ndarray: Noise reduced audio
        """
        # Compute STFT of input
        stft = librosa.stft(audio_data, n_fft=frame_length, hop_length=hop_length)
        spec = np.abs(stft)
        phase = np.angle(stft)
        
        # Apply spectral subtraction
        # Subtract noise profile scaled by strength
        spec_sub = np.maximum(
            spec - noise_profile * self.strength * 1.5,  # Adjust with strength factor
            0.01 * spec  # Spectral floor to avoid musical noise
        )
        
        # Reconstruct with ISTFT
        stft_sub = spec_sub * np.exp(1j * phase)
        audio_reduced = librosa.istft(stft_sub, hop_length=hop_length, length=len(audio_data))
        
        return audio_reduced
    
    def _adaptive_filter(self, audio_data, sr):
        """
        Apply adaptive filtering for further noise reduction.
        
        Args:
            audio_data (np.ndarray): Audio data
            sr (int): Sample rate
            
        Returns:
            np.ndarray: Filtered audio
        """
        # Simple adaptive filtering with balance controlled by strength
        # This is a basic implementation - could be enhanced with more advanced techniques
        
        # Design a bandpass filter focused on voice frequencies (300-3000 Hz)
        nyquist = 0.5 * sr
        low = 300 / nyquist
        high = 3000 / nyquist
        
        # Filter order adjusted by strength
        order = int(10 + self.strength * 10)
        
        # Apply bandpass filter
        b, a = signal.butter(order, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, audio_data)
        
        # Mix original and filtered based on strength
        return (1 - self.strength) * audio_data + self.strength * filtered
    
    def process(self, input_file, output_file=None):
        """
        Process an audio file to reduce noise.
        
        Args:
            input_file (str): Path to input audio file
            output_file (str, optional): Path to output file. If None, 
                                        will use input filename + "_nr"
                                        
        Returns:
            str: Path to the processed file
        """
        if output_file is None:
            filename, ext = os.path.splitext(input_file)
            output_file = f"{filename}_nr{ext}"
        
        try:
            logging.info(f"Starting noise reduction on {input_file}")
            
            # Load audio file
            audio_data, sr = librosa.load(input_file, sr=None, mono=False)
            
            # Convert to mono if needed for processing
            is_mono = len(audio_data.shape) == 1
            if not is_mono:
                # Process each channel separately
                channels = []
                for channel in range(audio_data.shape[0]):
                    channel_data = audio_data[channel]
                    noise_profile = self._estimate_noise_profile(channel_data, sr)
                    reduced = self._spectral_subtraction(channel_data, sr, noise_profile)
                    filtered = self._adaptive_filter(reduced, sr)
                    channels.append(filtered)
                processed_audio = np.array(channels)
            else:
                # Process mono file
                noise_profile = self._estimate_noise_profile(audio_data, sr)
                reduced = self._spectral_subtraction(audio_data, sr, noise_profile)
                processed_audio = self._adaptive_filter(reduced, sr)
            
            # Save processed audio
            sf.write(output_file, processed_audio.T if not is_mono else processed_audio, sr)
            logging.info(f"Noise reduction complete, saved to {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error during noise reduction: {e}")
            raise 