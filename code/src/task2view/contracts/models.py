"""Shared exception type."""


class PipelineError(ValueError):
    """A contract, input, or model-reply failure the pipeline reports instead of crashing."""
