import torch
from diffusers import StableDiffusionPipeline
import uuid
import os

MODEL_ID = "runwayml/stable-diffusion-v1-5"
OUTPUT_DIR = "outputs"


def run_stable_diffusion(prompt: str, steps: int = 30) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipe = StableDiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    )

    pipe = pipe.to(device)

    image = pipe(
        prompt,
        num_inference_steps=steps,
    ).images[0]

    filename = f"{uuid.uuid4().hex}.png"
    output_path = os.path.join(OUTPUT_DIR, filename)
    image.save(output_path)

    return output_path
