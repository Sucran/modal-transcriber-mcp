"""
Podcast Download Service - unified download functionality for multiple platforms
"""

import os
import re
import asyncio
import subprocess
import pathlib
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ..interfaces.podcast_downloader import (
    IPodcastDownloader,
    PodcastInfo,
    DownloadResult,
    PodcastPlatform
)
from ..utils.errors import FileProcessingError, ConfigurationError
from ..models.download import DownloadResponse


class PodcastDownloadService(IPodcastDownloader):
    """Unified podcast download service supporting multiple platforms"""
    
    def __init__(self, default_output_folder: str = None):
        # Use storage config if no folder specified
        if default_output_folder is None:
            from ..utils.storage_config import get_storage_config
            storage_config = get_storage_config()
            self.default_output_folder = str(storage_config.downloads_dir)
        else:
            self.default_output_folder = default_output_folder
            
        self.supported_platforms = {
            PodcastPlatform.APPLE: self._handle_apple_podcast,
            PodcastPlatform.XIAOYUZHOU: self._handle_xiaoyuzhou_podcast
        }
    
    async def extract_podcast_info(self, url: str) -> PodcastInfo:
        """Extract podcast information from URL"""
        
        platform = self._detect_platform(url)
        
        if platform == PodcastPlatform.APPLE:
            return await self._extract_apple_info(url)
        elif platform == PodcastPlatform.XIAOYUZHOU:
            return await self._extract_xiaoyuzhou_info(url)
        else:
            raise ConfigurationError(f"Unsupported platform for URL: {url}")
    
    async def download_podcast(
        self,
        url: str,
        output_folder: str = None,
        convert_to_mp3: bool = False,
        keep_original: bool = False
    ) -> DownloadResult:
        """Download podcast from URL"""
        
        output_folder = output_folder or self.default_output_folder
        
        try:
            # Ensure output folder exists
            pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)
            
            # Detect platform and use appropriate handler
            platform = self._detect_platform(url)
            handler = self.supported_platforms.get(platform)
            
            if not handler:
                return DownloadResult(
                    success=False,
                    file_path=None,
                    podcast_info=None,
                    error_message=f"Unsupported platform for URL: {url}"
                )
            
            # Call platform-specific handler
            result = await handler(url, output_folder, convert_to_mp3, keep_original)
            return result
            
        except Exception as e:
            return DownloadResult(
                success=False,
                file_path=None,
                podcast_info=None,
                error_message=f"Download failed: {str(e)}"
            )
    
    def get_supported_platforms(self) -> list[PodcastPlatform]:
        """Get list of supported platforms"""
        return list(self.supported_platforms.keys())
    
    def can_handle_url(self, url: str) -> bool:
        """Check if this downloader can handle the given URL"""
        try:
            platform = self._detect_platform(url)
            return platform in self.supported_platforms
        except:
            return False
    
    def _detect_platform(self, url: str) -> PodcastPlatform:
        """Detect platform from URL"""
        
        if "podcasts.apple.com" in url:
            return PodcastPlatform.APPLE
        elif "xiaoyuzhoufm.com" in url:
            return PodcastPlatform.XIAOYUZHOU
        else:
            return PodcastPlatform.GENERIC
    
    async def _extract_apple_info(self, url: str) -> PodcastInfo:
        """Extract Apple Podcast information"""
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, requests.get, url)
        
        if response.status_code != 200:
            raise FileProcessingError(f"Failed to fetch podcast page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find audio URL
        audio_url = self._find_audio_url_in_html(response.text)
        if not audio_url:
            raise FileProcessingError("Unable to find podcast audio URL")
        
        # Find title
        title = self._extract_apple_title(soup)
        if not title:
            raise FileProcessingError("Unable to find podcast title")
        
        # Extract episode ID
        episode_id = self._extract_apple_episode_id(url)
        
        return PodcastInfo(
            title=title,
            audio_url=audio_url,
            episode_id=episode_id,
            platform=PodcastPlatform.APPLE
        )
    
    async def _extract_xiaoyuzhou_info(self, url: str) -> PodcastInfo:
        """Extract XiaoYuZhou Podcast information"""
        
        loop = asyncio.get_event_loop()
        
        # Use similar extraction logic as original
        # This would need to be implemented based on XiaoYuZhou's page structure
        try:
            response = await loop.run_in_executor(None, requests.get, url)
            
            if response.status_code != 200:
                raise FileProcessingError(f"Failed to fetch XYZ podcast page: {response.status_code}")
            
            # Extract info from response (implementation depends on XYZ structure)
            # For now, return a basic structure
            episode_id = self._extract_xyz_episode_id(url)
            
            return PodcastInfo(
                title=f"XYZ Episode {episode_id}",
                audio_url="",  # Would be extracted from page
                episode_id=episode_id,
                platform=PodcastPlatform.XIAOYUZHOU
            )
        except Exception as e:
            raise FileProcessingError(f"XiaoYuZhou info extraction failed: {str(e)}")
    
    async def _handle_apple_podcast(
        self,
        url: str,
        output_folder: str,
        convert_to_mp3: bool,
        keep_original: bool
    ) -> DownloadResult:
        """Handle Apple Podcast download"""
        
        try:
            # Extract podcast info
            podcast_info = await self._extract_apple_info(url)
            
            # Generate output filename
            output_file = self._generate_filename(
                podcast_info.episode_id,
                podcast_info.audio_url,
                output_folder,
                convert_to_mp3
            )
            
            # Download audio file
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._download_file,
                podcast_info.audio_url,
                output_file
            )
            
            # Convert to MP3 if requested
            if convert_to_mp3:
                output_file = await self._convert_to_mp3(output_file, keep_original)
            
            return DownloadResult(
                success=True,
                file_path=output_file,
                podcast_info=podcast_info
            )
            
        except Exception as e:
            return DownloadResult(
                success=False,
                file_path=None,
                podcast_info=None,
                error_message=str(e)
            )
    
    async def _handle_xiaoyuzhou_podcast(
        self,
        url: str,
        output_folder: str,
        convert_to_mp3: bool,
        keep_original: bool
    ) -> DownloadResult:
        """Handle XiaoYuZhou Podcast download"""
        
        try:
            # Use our internal implementation instead of importing from methods
            audio_path, title = await self._download_xiaoyuzhou_episode(url, output_folder)
            
            # Extract episode ID
            episode_id = self._extract_xyz_episode_id(url)
            
            podcast_info = PodcastInfo(
                title=title or f"XYZ Episode {episode_id}",
                audio_url="",  # Not available from the function
                episode_id=episode_id,
                platform=PodcastPlatform.XIAOYUZHOU
            )
            
            return DownloadResult(
                success=True,
                file_path=audio_path,
                podcast_info=podcast_info
            )
            
        except Exception as e:
            return DownloadResult(
                success=False,
                file_path=None,
                podcast_info=None,
                error_message=str(e)
            )
    
    async def _download_xiaoyuzhou_episode(self, url: str, output_folder: str) -> tuple[str, str]:
        """Download XiaoYuZhou episode using Selenium"""
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from bs4 import BeautifulSoup
        import requests
        import json
        import os
        import time
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize driver
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit more for JavaScript to execute
            time.sleep(3)
            
            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract episode title
            title = "Unknown Episode"
            title_selectors = [
                'h1[data-v-]',
                '.episode-title',
                'h1',
                '.title'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.text.strip():
                    title = title_elem.text.strip()
                    break
            
            # Try to find audio URL in the page source or network requests
            audio_url = None
            
            # Look for audio URLs in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for audio file URLs
                    import re
                    audio_matches = re.findall(r'https://[^\s"\']+\.mp3[^\s"\']*', script.string)
                    if audio_matches:
                        audio_url = audio_matches[0]
                        break
            
            if not audio_url:
                # Alternative: try to find audio element or data attributes
                audio_elements = soup.find_all(['audio', 'source'])
                for audio_elem in audio_elements:
                    src = audio_elem.get('src') or audio_elem.get('data-src')
                    if src and ('.mp3' in src or '.m4a' in src):
                        audio_url = src
                        break
            
            if not audio_url:
                raise Exception("Could not find audio URL in the page")
            
            # Extract episode ID for filename
            episode_id = self._extract_xyz_episode_id(url)
            filename = f"{episode_id}_xiaoyuzhou_episode.mp3"
            output_path = os.path.join(output_folder, filename)
            
            # Ensure output directory exists
            os.makedirs(output_folder, exist_ok=True)
            
            # Download the audio file
            await self._download_file_async(audio_url, output_path)
            
            return output_path, title
            
        except Exception as e:
            raise Exception(f"XiaoYuZhou download failed: {str(e)}")
        
        finally:
            if driver:
                driver.quit()
    
    async def _download_file_async(self, url: str, output_path: str) -> None:
        """Download file from URL asynchronously"""
        
        import aiohttp
        import asyncio
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
    
    def _find_audio_url_in_html(self, html: str) -> Optional[str]:
        """Find audio URL in HTML content"""
        
        # Find all .mp3 and .m4a URLs
        audio_urls = re.findall(r'https://[^\s^"]+(?:\.mp3|\.m4a)', html)
        
        if audio_urls:
            pattern = r'=https?://[^\s^"]+(?:\.mp3|\.m4a)'
            result = re.findall(pattern, audio_urls[-1])
            if result:
                return result[-1][1:]
            else:
                return audio_urls[-1]
        
        return None
    
    def _extract_apple_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from Apple Podcast page"""
        
        title_selectors = [
            'span.product-header__title',
            'h1.product-header__title',
            '.product-header__title',
            'h1[data-testid="product-header-title"]',
            '.headings__title',
            'h1.headings__title',
            '.episode-title',
            'h1'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.text.strip().replace('/', '-')
        
        # Fallback to page title
        page_title = soup.find('title')
        if page_title:
            return page_title.text.strip().replace('/', '-').replace(' on Apple Podcasts', '')
        
        return None
    
    def _extract_apple_episode_id(self, url: str) -> str:
        """Extract episode ID from Apple Podcast URL"""
        
        # Try to extract episode ID from URL
        episode_match = re.search(r'[?&]i=(\d+)', url)
        if episode_match:
            return episode_match.group(1)
        
        # Try podcast ID
        podcast_match = re.search(r'/id(\d+)', url)
        if podcast_match:
            return podcast_match.group(1)
        
        # Fallback to timestamp
        import time
        return str(int(time.time()))
    
    def _extract_xyz_episode_id(self, url: str) -> str:
        """Extract episode ID from XiaoYuZhou URL"""
        
        episode_match = re.search(r'/episode/([^/?]+)', url)
        if episode_match:
            return episode_match.group(1)
        
        # Fallback
        import time
        return str(int(time.time()))
    
    def _generate_filename(
        self,
        episode_id: str,
        audio_url: str,
        output_folder: str,
        convert_to_mp3: bool
    ) -> str:
        """Generate output filename"""
        
        if convert_to_mp3:
            extension = ".mp3"
        else:
            # Extract extension from URL
            parsed_url = urlparse(audio_url)
            _, extension = os.path.splitext(parsed_url.path)
            if not extension:
                extension = ".mp3"
        
        filename = f"{episode_id}_episode_audio{extension}"
        return os.path.join(output_folder, filename)
    
    def _download_file(self, url: str, output_path: str) -> None:
        """Download file from URL"""
        
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
    
    async def _convert_to_mp3(
        self,
        input_file: str,
        keep_original: bool = False
    ) -> str:
        """Convert audio file to MP3 format"""
        
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.mp3"
        
        if input_file == output_file:
            return input_file  # Already MP3
        
        try:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-codec:a', 'libmp3lame',
                '-b:a', '128k',
                '-y',
                output_file
            ]
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                subprocess.run,
                cmd,
                True,  # capture_output
                True   # text
            )
            
            if result.returncode == 0:
                print(f"Successfully converted to: {output_file}")
                
                if not keep_original:
                    os.remove(input_file)
                    print(f"Removed original file: {input_file}")
                
                return output_file
            else:
                print(f"Error converting file: {result.stderr}")
                return input_file
                
        except Exception as e:
            print(f"Error during conversion: {str(e)}")
            return input_file 