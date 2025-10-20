#!/usr/bin/env python3
"""
YOLOv8 training script for weed detection.

This script trains a YOLOv8 model on weed detection datasets.
"""

import sys
import argparse
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class YOLOTrainer:
    """YOLOv8 model trainer for weed detection."""

    def __init__(
        self,
        data_yaml: str,
        model_size: str = 'n',
        epochs: int = 100,
        batch_size: int = 16,
        img_size: int = 640,
        device: str = '0'
    ):
        """
        Initialize trainer.

        Args:
            data_yaml: Path to data.yaml configuration
            model_size: Model size (n, s, m, l, x)
            epochs: Number of training epochs
            batch_size: Batch size
            img_size: Input image size
            device: Device to use (0 for GPU, cpu for CPU)
        """
        self.data_yaml = Path(data_yaml)
        self.model_size = model_size
        self.epochs = epochs
        self.batch_size = batch_size
        self.img_size = img_size
        self.device = device

        # Validate data.yaml
        if not self.data_yaml.exists():
            raise FileNotFoundError(f"Data config not found: {self.data_yaml}")

        logger.info(f"Initializing YOLOv8{model_size} trainer")
        logger.info(f"Dataset: {self.data_yaml}")

    def train(
        self,
        pretrained: bool = True,
        patience: int = 50,
        save_period: int = 10,
        project: str = 'runs/train',
        name: str = 'weed_detection',
        **kwargs
    ):
        """
        Train YOLOv8 model.

        Args:
            pretrained: Use pretrained weights
            patience: Early stopping patience
            save_period: Save checkpoint every N epochs
            project: Project directory
            name: Experiment name
            **kwargs: Additional training arguments
        """
        try:
            from ultralytics import YOLO

            # Initialize model
            model_name = f'yolov8{self.model_size}.pt' if pretrained else f'yolov8{self.model_size}.yaml'
            logger.info(f"Loading model: {model_name}")

            model = YOLO(model_name)

            # Training arguments
            train_args = {
                'data': str(self.data_yaml),
                'epochs': self.epochs,
                'batch': self.batch_size,
                'imgsz': self.img_size,
                'device': self.device,
                'patience': patience,
                'save_period': save_period,
                'project': project,
                'name': name,
                'pretrained': pretrained,
                'optimizer': 'AdamW',
                'lr0': 0.01,
                'lrf': 0.01,
                'momentum': 0.937,
                'weight_decay': 0.0005,
                'warmup_epochs': 3,
                'warmup_momentum': 0.8,
                'warmup_bias_lr': 0.1,
                'box': 7.5,
                'cls': 0.5,
                'dfl': 1.5,
                'pose': 12.0,
                'kobj': 1.0,
                'label_smoothing': 0.0,
                'nbs': 64,
                'hsv_h': 0.015,
                'hsv_s': 0.7,
                'hsv_v': 0.4,
                'degrees': 0.0,
                'translate': 0.1,
                'scale': 0.5,
                'shear': 0.0,
                'perspective': 0.0,
                'flipud': 0.0,
                'fliplr': 0.5,
                'mosaic': 1.0,
                'mixup': 0.0,
                'copy_paste': 0.0,
                **kwargs
            }

            logger.info("Starting training...")
            logger.info(f"Training arguments: {train_args}")

            # Train model
            results = model.train(**train_args)

            logger.info("Training completed!")
            logger.info(f"Results saved to: {project}/{name}")

            return results

        except ImportError:
            logger.error("Ultralytics not installed!")
            print("\n❌ Error: Ultralytics library not installed")
            print("Install with: pip install ultralytics")
            return None
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

    def validate(self, weights: str, split: str = 'val'):
        """
        Validate trained model.

        Args:
            weights: Path to trained weights
            split: Dataset split to validate on (val/test)
        """
        try:
            from ultralytics import YOLO

            logger.info(f"Validating model: {weights}")

            model = YOLO(weights)
            results = model.val(
                data=str(self.data_yaml),
                split=split,
                batch=self.batch_size,
                imgsz=self.img_size,
                device=self.device
            )

            logger.info("Validation completed!")
            return results

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise

    def export(
        self,
        weights: str,
        format: str = 'tflite',
        int8: bool = False,
        half: bool = False
    ):
        """
        Export trained model to different formats.

        Args:
            weights: Path to trained weights
            format: Export format (tflite, onnx, engine, coreml, etc.)
            int8: Use INT8 quantization (TFLite only)
            half: Use FP16 precision
        """
        try:
            from ultralytics import YOLO

            logger.info(f"Exporting model to {format}")

            model = YOLO(weights)
            export_path = model.export(
                format=format,
                int8=int8,
                half=half,
                imgsz=self.img_size
            )

            logger.info(f"Model exported to: {export_path}")
            return export_path

        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise

    def create_data_yaml(
        self,
        train_dir: str,
        val_dir: str,
        test_dir: str = None,
        class_names: list = None,
        output_path: str = None
    ):
        """
        Create data.yaml configuration file.

        Args:
            train_dir: Training images directory
            val_dir: Validation images directory
            test_dir: Test images directory (optional)
            class_names: List of class names
            output_path: Output path for data.yaml
        """
        if class_names is None:
            class_names = ['weed', 'crop']

        data_config = {
            'path': str(Path(train_dir).parent.absolute()),
            'train': str(Path(train_dir).name),
            'val': str(Path(val_dir).name),
            'nc': len(class_names),
            'names': class_names
        }

        if test_dir:
            data_config['test'] = str(Path(test_dir).name)

        output_path = output_path or 'data.yaml'
        with open(output_path, 'w') as f:
            yaml.dump(data_config, f, sort_keys=False)

        logger.info(f"Created data.yaml: {output_path}")
        print(f"\n✅ Created data configuration: {output_path}")

        return output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Train YOLOv8 model for weed detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train YOLOv8n (nano) model
  python train_yolo.py --data data/datasets/sample/data.yaml

  # Train YOLOv8s (small) model with custom parameters
  python train_yolo.py --data data/datasets/sample/data.yaml --model s --epochs 150 --batch 32

  # Validate trained model
  python train_yolo.py --validate --weights runs/train/weed_detection/weights/best.pt

  # Export model to TFLite
  python train_yolo.py --export --weights runs/train/weed_detection/weights/best.pt --format tflite

  # Export with INT8 quantization
  python train_yolo.py --export --weights runs/train/weed_detection/weights/best.pt --format tflite --int8
        """
    )

    # Common arguments
    parser.add_argument(
        '--data',
        type=str,
        help='Path to data.yaml'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='n',
        choices=['n', 's', 'm', 'l', 'x'],
        help='Model size (n=nano, s=small, m=medium, l=large, x=xlarge)'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='0',
        help='Device to use (0 for GPU, cpu for CPU)'
    )
    parser.add_argument(
        '--img-size',
        type=int,
        default=640,
        help='Input image size'
    )

    # Training arguments
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch',
        type=int,
        default=16,
        help='Batch size'
    )
    parser.add_argument(
        '--patience',
        type=int,
        default=50,
        help='Early stopping patience'
    )
    parser.add_argument(
        '--no-pretrained',
        action='store_true',
        help='Train from scratch (no pretrained weights)'
    )
    parser.add_argument(
        '--project',
        type=str,
        default='runs/train',
        help='Project directory'
    )
    parser.add_argument(
        '--name',
        type=str,
        default='weed_detection',
        help='Experiment name'
    )

    # Validation arguments
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate trained model'
    )
    parser.add_argument(
        '--weights',
        type=str,
        help='Path to weights for validation/export'
    )

    # Export arguments
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export trained model'
    )
    parser.add_argument(
        '--format',
        type=str,
        default='tflite',
        choices=['tflite', 'onnx', 'engine', 'coreml', 'pb'],
        help='Export format'
    )
    parser.add_argument(
        '--int8',
        action='store_true',
        help='Use INT8 quantization (TFLite)'
    )
    parser.add_argument(
        '--half',
        action='store_true',
        help='Use FP16 precision'
    )

    args = parser.parse_args()

    # Setup logging
    app_logger.setup(log_level='INFO')

    # Validate mode
    if args.validate:
        if not args.weights:
            parser.error("--weights required for validation")
        if not args.data:
            parser.error("--data required for validation")

        trainer = YOLOTrainer(
            data_yaml=args.data,
            model_size=args.model,
            batch_size=args.batch,
            img_size=args.img_size,
            device=args.device
        )
        trainer.validate(args.weights)
        return

    # Export mode
    if args.export:
        if not args.weights:
            parser.error("--weights required for export")

        trainer = YOLOTrainer(
            data_yaml=args.data or 'data.yaml',
            model_size=args.model,
            img_size=args.img_size
        )
        export_path = trainer.export(
            args.weights,
            format=args.format,
            int8=args.int8,
            half=args.half
        )
        print(f"\n🎉 Model exported to: {export_path}")
        return

    # Training mode
    if not args.data:
        parser.error("--data required for training")

    trainer = YOLOTrainer(
        data_yaml=args.data,
        model_size=args.model,
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.img_size,
        device=args.device
    )

    print("\n🚀 Starting YOLOv8 training for weed detection...")
    print(f"   Model: YOLOv8{args.model}")
    print(f"   Dataset: {args.data}")
    print(f"   Epochs: {args.epochs}")
    print(f"   Batch size: {args.batch}")
    print(f"   Image size: {args.img_size}")
    print(f"   Device: {args.device}\n")

    results = trainer.train(
        pretrained=not args.no_pretrained,
        patience=args.patience,
        project=args.project,
        name=args.name
    )

    if results:
        print("\n🎉 Training completed successfully!")
        print(f"\n📁 Results saved to: {args.project}/{args.name}")
        print("\n📊 Next steps:")
        print(f"   1. Validate: python train_yolo.py --validate --weights {args.project}/{args.name}/weights/best.pt --data {args.data}")
        print(f"   2. Export: python train_yolo.py --export --weights {args.project}/{args.name}/weights/best.pt --format tflite")


if __name__ == '__main__':
    main()
