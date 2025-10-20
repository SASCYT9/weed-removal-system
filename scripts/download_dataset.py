#!/usr/bin/env python3
"""
Dataset downloader for weed detection training.

Supports multiple public weed detection datasets:
1. DeepWeeds Dataset (Australia)
2. CottonWeeds Dataset
3. Crop/Weed Field Image Dataset (CWFID)
4. Roboflow Weed Detection datasets
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from tqdm import tqdm
import zipfile
import tarfile
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class DatasetDownloader:
    """Download and prepare weed detection datasets."""

    # Public datasets with direct download links
    DATASETS = {
        'deepweeds': {
            'name': 'DeepWeeds Dataset',
            'description': '17,509 images of 8 weed species from Australia',
            'url': 'https://nextcloud.qriscloud.org.au/index.php/s/a3KxPawpqkiorST/download',
            'format': 'zip',
            'size': '1.4 GB',
            'classes': ['Chinee apple', 'Lantana', 'Parkinsonia', 'Parthenium',
                       'Prickly acacia', 'Rubber vine', 'Siam weed', 'Snake weed', 'Negative']
        },
        'cwfid': {
            'name': 'Crop/Weed Field Image Dataset',
            'description': 'Field images with crop and weed annotations',
            'url': 'https://github.com/cwfid/dataset',
            'format': 'manual',
            'size': 'Various',
            'classes': ['crop', 'weed']
        },
        'roboflow-agriculture': {
            'name': 'Roboflow Agriculture Dataset',
            'description': 'Pre-annotated weed detection dataset from Roboflow',
            'url': 'roboflow',  # Requires API key
            'format': 'roboflow',
            'size': 'Various',
            'classes': ['weed', 'crop']
        }
    }

    def __init__(self, output_dir: str = 'data/datasets'):
        """
        Initialize dataset downloader.

        Args:
            output_dir: Directory to save datasets
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Dataset output directory: {self.output_dir}")

    def list_datasets(self):
        """List available datasets."""
        print("\n📦 Available Weed Detection Datasets:\n")
        for key, info in self.DATASETS.items():
            print(f"  {key}:")
            print(f"    Name: {info['name']}")
            print(f"    Description: {info['description']}")
            print(f"    Size: {info['size']}")
            print(f"    Classes: {', '.join(info['classes'])}")
            print()

    def download_file(self, url: str, output_path: Path, desc: str = None):
        """
        Download file with progress bar.

        Args:
            url: URL to download
            output_path: Path to save file
            desc: Description for progress bar
        """
        logger.info(f"Downloading from {url}")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f, tqdm(
            desc=desc or output_path.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

        logger.info(f"Downloaded to {output_path}")

    def extract_archive(self, archive_path: Path, extract_to: Path):
        """
        Extract archive file.

        Args:
            archive_path: Path to archive
            extract_to: Directory to extract to
        """
        logger.info(f"Extracting {archive_path}")

        if archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.suffix in ['.tar', '.gz', '.tgz']:
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            raise ValueError(f"Unsupported archive format: {archive_path.suffix}")

        logger.info(f"Extracted to {extract_to}")

    def download_deepweeds(self):
        """Download DeepWeeds dataset."""
        dataset_dir = self.output_dir / 'deepweeds'
        dataset_dir.mkdir(exist_ok=True)

        archive_path = dataset_dir / 'deepweeds.zip'

        print("\n🌿 Downloading DeepWeeds Dataset...")
        print("This is a large dataset (1.4 GB), please be patient.\n")

        try:
            self.download_file(
                self.DATASETS['deepweeds']['url'],
                archive_path,
                desc="DeepWeeds"
            )

            print("\n📦 Extracting dataset...")
            self.extract_archive(archive_path, dataset_dir)

            # Clean up archive
            archive_path.unlink()

            print(f"\n✅ DeepWeeds dataset downloaded to: {dataset_dir}")
            return dataset_dir

        except Exception as e:
            logger.error(f"Failed to download DeepWeeds: {e}")
            print(f"\n❌ Error: {e}")
            return None

    def download_roboflow(self, api_key: str = None, workspace: str = None, project: str = None):
        """
        Download dataset from Roboflow.

        Args:
            api_key: Roboflow API key
            workspace: Roboflow workspace
            project: Roboflow project name
        """
        if not api_key:
            print("\n⚠️  Roboflow API key required!")
            print("Get your API key from: https://roboflow.com/")
            print("\nExample usage:")
            print("  python download_dataset.py roboflow-agriculture --api-key YOUR_KEY")
            return None

        try:
            from roboflow import Roboflow

            rf = Roboflow(api_key=api_key)

            # Default to agriculture-related project if not specified
            if not workspace or not project:
                print("\n📝 Using default Roboflow agriculture dataset")
                workspace = workspace or "roboflow-universe"
                project = project or "weed-detection"

            project_obj = rf.workspace(workspace).project(project)
            dataset = project_obj.version(1).download("yolov8")

            print(f"\n✅ Roboflow dataset downloaded to: {dataset.location}")
            return Path(dataset.location)

        except ImportError:
            print("\n❌ Roboflow library not installed!")
            print("Install with: pip install roboflow")
            return None
        except Exception as e:
            logger.error(f"Failed to download from Roboflow: {e}")
            print(f"\n❌ Error: {e}")
            return None

    def create_sample_dataset(self):
        """Create a small sample dataset for testing."""
        sample_dir = self.output_dir / 'sample'
        sample_dir.mkdir(exist_ok=True)

        print("\n🔬 Creating sample dataset structure...")

        # Create directory structure
        for split in ['train', 'val', 'test']:
            (sample_dir / split / 'images').mkdir(parents=True, exist_ok=True)
            (sample_dir / split / 'labels').mkdir(parents=True, exist_ok=True)

        # Create data.yaml
        data_yaml = {
            'path': str(sample_dir.absolute()),
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'nc': 2,
            'names': ['weed', 'crop']
        }

        with open(sample_dir / 'data.yaml', 'w') as f:
            import yaml
            yaml.dump(data_yaml, f)

        print(f"\n✅ Sample dataset structure created at: {sample_dir}")
        print("\n📝 Add your images and labels to:")
        print(f"  - {sample_dir}/train/images/ (and labels)")
        print(f"  - {sample_dir}/val/images/ (and labels)")
        print(f"  - {sample_dir}/test/images/ (and labels)")

        return sample_dir

    def download(self, dataset_name: str, **kwargs):
        """
        Download specified dataset.

        Args:
            dataset_name: Name of dataset to download
            **kwargs: Additional arguments for specific datasets
        """
        if dataset_name not in self.DATASETS:
            logger.error(f"Unknown dataset: {dataset_name}")
            print(f"\n❌ Unknown dataset: {dataset_name}")
            print("Run with --list to see available datasets")
            return None

        if dataset_name == 'deepweeds':
            return self.download_deepweeds()
        elif dataset_name == 'roboflow-agriculture':
            return self.download_roboflow(**kwargs)
        elif dataset_name == 'sample':
            return self.create_sample_dataset()
        else:
            info = self.DATASETS[dataset_name]
            print(f"\n📖 {info['name']}")
            print(f"   {info['description']}")
            print(f"\n⚠️  Manual download required:")
            print(f"   URL: {info['url']}")
            return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download weed detection datasets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available datasets
  python download_dataset.py --list

  # Download DeepWeeds dataset
  python download_dataset.py deepweeds

  # Download from Roboflow (requires API key)
  python download_dataset.py roboflow-agriculture --api-key YOUR_KEY

  # Create sample dataset structure
  python download_dataset.py sample
        """
    )

    parser.add_argument(
        'dataset',
        nargs='?',
        help='Dataset name to download'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available datasets'
    )
    parser.add_argument(
        '--output-dir',
        default='data/datasets',
        help='Output directory for datasets'
    )
    parser.add_argument(
        '--api-key',
        help='API key for Roboflow datasets'
    )

    args = parser.parse_args()

    # Setup logging
    app_logger.setup(log_level='INFO')

    downloader = DatasetDownloader(args.output_dir)

    if args.list:
        downloader.list_datasets()
        return

    if not args.dataset:
        parser.print_help()
        return

    # Download dataset
    result = downloader.download(
        args.dataset,
        api_key=args.api_key
    )

    if result:
        print("\n🎉 Dataset ready for training!")


if __name__ == '__main__':
    main()
