from appconfigpy import ConfigItem, ConfigManager, DefaultDisplayStyle

from ._const import Default


app_config_mgr = ConfigManager(
    config_name=Default.CONFIG_FILENAME,
    config_items=[
        ConfigItem(
            name="token",
            initial_value=None,
            prompt_text="personal access token",
            default_display_style=DefaultDisplayStyle.PART_VISIBLE,
            required=True,
        )
    ],
)
