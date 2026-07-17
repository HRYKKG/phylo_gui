def run_pipeline_windows(context, start_stage="alignment"):
    """Run pipeline windows from one loop so Back/Next does not grow the call stack."""
    stage = start_stage
    while stage:
        if stage == "alignment":
            from ui_alignment import open_alignment_options_window

            stage = open_alignment_options_window(context)
        elif stage == "trim":
            from ui_trim import open_trim_options_window

            stage = open_trim_options_window(context)
        elif stage == "iqtree":
            from ui_iqtree import open_iqtree_options_window

            stage = open_iqtree_options_window(context)
        else:
            raise ValueError(f"Unknown pipeline stage: {stage}")
