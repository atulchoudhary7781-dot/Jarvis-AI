# jarvis_themes.py - Enhanced UI Customization & Themes
# Provides multiple customizable color themes for JARVIS
import logging

from typing import Dict, Optional, Tuple


class ThemeManager:
    """
    Manages multiple UI color themes for customization.
    Provides pre-built themes and allows custom theme creation.
    """
    
    # Theme color palettes
    THEMES = {
        "Classic": {
            "name": "Classic",
            "description": "Default professional dark theme",
            "primary_color": "#4a5fe8",
            "primary_hover": "#3a4fd8",
            "secondary_color": "#2a2a35",
            "background": "#0a0a12",
            "sidebar_bg": "#0a0a12",
            "text_primary": "#ffffff",
            "text_secondary": "#888888",
            "accent": "#4a5fe8",
            "border_color": "#333333",
            "chat_user_bg": "#4a5fe8",
            "chat_assistant_bg": "#1a1a1a",
        },
        
        "Cyberpunk": {
            "name": "Cyberpunk",
            "description": "Futuristic neon theme with bright accents",
            "primary_color": "#ff006e",
            "primary_hover": "#e6005c",
            "secondary_color": "#8338ec",
            "background": "#030013",
            "sidebar_bg": "#050020",
            "text_primary": "#fbf5ff",
            "text_secondary": "#b8a8ff",
            "accent": "#00f5ff",
            "border_color": "#8338ec",
            "chat_user_bg": "#ff006e",
            "chat_assistant_bg": "#1a0a2e",
        },
        
        "Minimalist": {
            "name": "Minimalist",
            "description": "Clean, simple light and neutral theme",
            "primary_color": "#1a1a1a",
            "primary_hover": "#333333",
            "secondary_color": "#f5f5f5",
            "background": "#ffffff",
            "sidebar_bg": "#f9f9f9",
            "text_primary": "#1a1a1a",
            "text_secondary": "#999999",
            "accent": "#666666",
            "border_color": "#e0e0e0",
            "chat_user_bg": "#e8e8e8",
            "chat_assistant_bg": "#f5f5f5",
        },
        
        "Iron Man": {
            "name": "Iron Man",
            "description": "Gold and black theme inspired by Iron Man",
            "primary_color": "#ffd700",
            "primary_hover": "#ffed4e",
            "secondary_color": "#1a1a1a",
            "background": "#0d0d0d",
            "sidebar_bg": "#1a1a1a",
            "text_primary": "#ffd700",
            "text_secondary": "#888888",
            "accent": "#ffd700",
            "border_color": "#ffd700",
            "chat_user_bg": "#ffd700",
            "chat_assistant_bg": "#1a1a1a",
        },
        
        "Ocean": {
            "name": "Ocean",
            "description": "Cool blues and teals inspired by ocean",
            "primary_color": "#00d4ff",
            "primary_hover": "#00b8d4",
            "secondary_color": "#0a2540",
            "background": "#051428",
            "sidebar_bg": "#061b3f",
            "text_primary": "#ffffff",
            "text_secondary": "#7da8c4",
            "accent": "#00d4ff",
            "border_color": "#086a96",
            "chat_user_bg": "#00d4ff",
            "chat_assistant_bg": "#0f3a5f",
        },
        
        "Forest": {
            "name": "Forest",
            "description": "Natural greens and earth tones",
            "primary_color": "#2d6a4f",
            "primary_hover": "#1b4332",
            "secondary_color": "#40916c",
            "background": "#081c15",
            "sidebar_bg": "#1b4332",
            "text_primary": "#d8f3dc",
            "text_secondary": "#95b8a1",
            "accent": "#52b788",
            "border_color": "#2d6a4f",
            "chat_user_bg": "#52b788",
            "chat_assistant_bg": "#1b4332",
        },
        
        "Sunset": {
            "name": "Sunset",
            "description": "Warm oranges and purples like a sunset",
            "primary_color": "#ff6b35",
            "primary_hover": "#f7931e",
            "secondary_color": "#2d1b3d",
            "background": "#1a0e2e",
            "sidebar_bg": "#16213e",
            "text_primary": "#ffa07a",
            "text_secondary": "#d4a574",
            "accent": "#ff6b35",
            "border_color": "#6a4c93",
            "chat_user_bg": "#ff6b35",
            "chat_assistant_bg": "#2d1b3d",
        },
        
        "Nord": {
            "name": "Nord",
            "description": "Arctic, north-bluish color palette",
            "primary_color": "#88c0d0",
            "primary_hover": "#81a1c1",
            "secondary_color": "#2e3440",
            "background": "#2e3440",
            "sidebar_bg": "#3b4252",
            "text_primary": "#eceff4",
            "text_secondary": "#a3be8c",
            "accent": "#81a1c1",
            "border_color": "#4c566a",
            "chat_user_bg": "#88c0d0",
            "chat_assistant_bg": "#3b4252",
        },
    }
    
    def __init__(self, default_theme: str = "Classic"):
        self.current_theme = default_theme
        self.custom_themes: Dict[str, Dict] = {}
        
        if default_theme not in self.THEMES:
            logging.warning(f"Warning: Theme '{default_theme}' not found, using 'Classic'")
            self.current_theme = "Classic"
    
    def get_theme(self, theme_name: Optional[str] = None) -> Dict[str, str]:
        """
        Get theme colors by name.
        
        Args:
            theme_name: Theme name (default: current theme)
            
        Returns:
            Dictionary of color values
        """
        if theme_name is None:
            theme_name = self.current_theme
        
        # Check custom themes first
        if theme_name in self.custom_themes:
            return self.custom_themes[theme_name].copy()
        
        # Then check built-in themes
        if theme_name in self.THEMES:
            return self.THEMES[theme_name].copy()
        
        # Fallback to Classic
        return self.THEMES["Classic"].copy()
    
    def set_theme(self, theme_name: str) -> bool:
        """Set current theme."""
        if theme_name in self.THEMES or theme_name in self.custom_themes:
            self.current_theme = theme_name
            return True
        return False
    
    def list_themes(self) -> Dict[str, str]:
        """Get list of all available themes."""
        themes = {}
        
        # Built-in themes
        for name, colors in self.THEMES.items():
            themes[name] = colors.get("description", "")
        
        # Custom themes
        for name, colors in self.custom_themes.items():
            themes[name] = colors.get("description", "Custom")
        
        return themes
    
    def create_custom_theme(
        self,
        name: str,
        base_theme: str = "Classic",
        colors: Optional[Dict[str, str]] = None,
        description: str = "Custom theme"
    ) -> bool:
        """
        Create a custom theme based on an existing theme.
        
        Args:
            name: Custom theme name
            base_theme: Base theme to modify
            colors: Dictionary of colors to override
            description: Theme description
            
        Returns:
            Success boolean
        """
        if name in self.THEMES:
            logging.warning(f"Cannot override built-in theme '{name}'")
            return False
        
        # Get base theme
        base = self.get_theme(base_theme)
        
        # Override with custom colors
        if colors:
            base.update(colors)
        
        base["name"] = name
        base["description"] = description
        self.custom_themes[name] = base
        
        return True
    
    def get_color(self, key: str, theme_name: Optional[str] = None) -> str:
        """
        Get specific color value from theme.
        
        Args:
            key: Color key (e.g., "primary_color", "background")
            theme_name: Theme name (default: current theme)
            
        Returns:
            Hex color code
        """
        theme = self.get_theme(theme_name)
        return theme.get(key, "#ffffff")
    
    def get_all_colors(self, theme_name: Optional[str] = None) -> Dict[str, str]:
        """Get all color values for a theme."""
        return self.get_theme(theme_name)
    
    # Convenience methods for specific colors
    def primary_color(self, theme_name: Optional[str] = None) -> str:
        """Get primary color."""
        return self.get_color("primary_color", theme_name)
    
    def button_hover(self, theme_name: Optional[str] = None) -> str:
        """Get button hover color."""
        return self.get_color("primary_hover", theme_name)
    
    def background(self, theme_name: Optional[str] = None) -> str:
        """Get background color."""
        return self.get_color("background", theme_name)
    
    def sidebar_color(self, theme_name: Optional[str] = None) -> str:
        """Get sidebar background color."""
        return self.get_color("sidebar_bg", theme_name)
    
    def text_primary(self, theme_name: Optional[str] = None) -> str:
        """Get primary text color."""
        return self.get_color("text_primary", theme_name)
    
    def text_secondary(self, theme_name: Optional[str] = None) -> str:
        """Get secondary text color."""
        return self.get_color("text_secondary", theme_name)
    
    def accent_color(self, theme_name: Optional[str] = None) -> str:
        """Get accent color."""
        return self.get_color("accent", theme_name)
    
    def export_theme(self, theme_name: str) -> str:
        """Export theme as JSON string."""
        import json
        theme = self.get_theme(theme_name)
        return json.dumps(theme, indent=2)
    
    def import_theme_json(self, json_str: str, theme_name: str) -> bool:
        """Import theme from JSON string."""
        try:
            import json
            theme_data = json.loads(json_str)
            self.custom_themes[theme_name] = theme_data
            return True
        except Exception as e:
            logging.error(f"Failed to import theme: {e}", exc_info=True)
            return False
    
    def get_theme_contrast_ratio(self, color1: str, color2: str) -> float:
        """
        Calculate contrast ratio between two colors for accessibility.
        Higher is better (21:1 is excellent).
        """
        def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def relative_luminance(rgb: Tuple[int, int, int]) -> float:
            r, g, b = [x / 255.0 for x in rgb]
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        try:
            l1 = relative_luminance(hex_to_rgb(color1))
            l2 = relative_luminance(hex_to_rgb(color2))
            lighter = max(l1, l2)
            darker = min(l1, l2)
            return (lighter + 0.05) / (darker + 0.05)
        except Exception:
            return 0


# Example usage
if __name__ == "__main__":
    manager = ThemeManager()
    
    # List all themes
    logging.info("Available Themes:")
    for name, desc in manager.list_themes().items():
        logging.info(f"  {name}: {desc}")
    
    # Get current theme
    logging.info(f"\nCurrent theme: {manager.current_theme}")
    logging.info(f"Primary color: {manager.primary_color()}")
    
    # Create custom theme
    manager.create_custom_theme(
        "MyCustom",
        base_theme="Classic",
        colors={
            "primary_color": "#ff0000",
            "accent": "#00ff00"
        },
        description="My custom red and green theme"
    )
    logging.info(f"\nCreated custom theme: MyCustom")
    
    # Switch theme
    manager.set_theme("Cyberpunk")
    logging.info(f"Switched to theme: {manager.current_theme}")
    logging.info(f"Primary color: {manager.primary_color()}")
