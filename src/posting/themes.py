import uuid
from pydantic import BaseModel, Field
from rich.style import Style
from textual.color import Color
from textual.design import ColorSystem
from textual.theme import Theme as TextualTheme
from textual.widgets.text_area import TextAreaTheme
import yaml
from posting.config import SETTINGS


class PostingTextAreaTheme(BaseModel):
    gutter: str | None = Field(default=None)
    """The style to apply to the gutter."""

    cursor: str | None = Field(default=None)
    """The style to apply to the cursor."""

    cursor_line: str | None = Field(default=None)
    """The style to apply to the line the cursor is on."""

    cursor_line_gutter: str | None = Field(default=None)
    """The style to apply to the gutter of the line the cursor is on."""

    matched_bracket: str | None = Field(default=None)
    """The style to apply to bracket matching."""

    selection: str | None = Field(default=None)
    """The style to apply to the selected text."""


class SyntaxTheme(BaseModel):
    """Colours used in highlighting syntax in text areas and
    URL input fields."""

    json_key: str | None = Field(default=None)
    """The style to apply to JSON keys."""

    json_string: str | None = Field(default=None)
    """The style to apply to JSON strings."""

    json_number: str | None = Field(default=None)
    """The style to apply to JSON numbers."""

    json_boolean: str | None = Field(default=None)
    """The style to apply to JSON booleans."""

    json_null: str | None = Field(default=None)
    """The style to apply to JSON null values."""

    def to_text_area_syntax_styles(self, fallback_theme: "Theme") -> dict[str, Style]:
        """Convert this theme to a TextAreaTheme.

        If a fallback theme is provided, it will be used to fill in any missing
        styles.
        """
        syntax_styles = {
            "string": Style.parse(self.json_string or fallback_theme.primary),
            "number": Style.parse(self.json_number or fallback_theme.accent),
            "boolean": Style.parse(self.json_boolean or fallback_theme.accent),
            "json.null": Style.parse(self.json_null or fallback_theme.secondary),
            "json.label": (
                Style.parse(self.json_key or fallback_theme.primary) + Style(bold=True)
            ),
        }
        return syntax_styles


class VariableStyles(BaseModel):
    """The style to apply to variables."""

    resolved: str | None = Field(default=None)
    """The style to apply to resolved variables."""

    unresolved: str | None = Field(default=None)
    """The style to apply to unresolved variables."""

    def fill_with_defaults(self, theme: "Theme") -> "VariableStyles":
        """Return a new VariableStyles object with `None` values filled
        with reasonable defaults from the given theme."""
        return VariableStyles(
            resolved=self.resolved or theme.success,
            unresolved=self.unresolved or theme.error,
        )


class UrlStyles(BaseModel):
    """The style to apply to URL input fields."""

    base: str | None = Field(default=None)
    """The style to apply to the base of the URL."""

    protocol: str | None = Field(default=None)
    """The style to apply to the URL protocol."""

    separator: str | None = Field(default="dim")
    """The style to apply to URL separators e.g. `/`."""

    def fill_with_defaults(self, theme: "Theme") -> "UrlStyles":
        """Return a new UrlStyles object with `None` values filled
        with reasonable defaults from the given theme."""
        return UrlStyles(
            base=self.base or theme.secondary,
            protocol=self.protocol or theme.accent,
            separator=self.separator or "dim",
        )


class MethodStyles(BaseModel):
    """The style to apply to HTTP methods in the sidebar."""

    get: str | None = Field(default="#0ea5e9")
    post: str | None = Field(default="#22c55e")
    put: str | None = Field(default="#f59e0b")
    delete: str | None = Field(default="#ef4444")
    patch: str | None = Field(default="#14b8a6")
    options: str | None = Field(default="#8b5cf6")
    head: str | None = Field(default="#d946ef")


class Theme(BaseModel):
    name: str = Field(exclude=True)
    primary: str
    secondary: str | None = None
    background: str | None = None
    surface: str | None = None
    panel: str | None = None
    warning: str | None = None
    error: str | None = None
    success: str | None = None
    accent: str | None = None
    dark: bool = True

    text_area: PostingTextAreaTheme = Field(default_factory=PostingTextAreaTheme)
    """Styling to apply to TextAreas."""

    syntax: str | SyntaxTheme = Field(default="posting", exclude=True)
    """Posting can associate a syntax highlighting theme which will
    be switched to automatically when the app theme changes.
    
    This can either be a custom SyntaxTheme or a pre-defined Textual theme
    such as monokai, dracula, github_light, or vscode_dark. It can also be 'posting'
    which will use the posting theme as defined in themes.py."""

    url: UrlStyles | None = Field(default_factory=UrlStyles)
    """Styling to apply to URL input fields."""

    variable: VariableStyles | None = Field(default_factory=VariableStyles)
    """The style to apply to variables."""

    method: MethodStyles | None = Field(default_factory=MethodStyles)
    """The style to apply to HTTP methods in the sidebar."""

    # Optional metadata
    author: str | None = Field(default=None, exclude=True)
    description: str | None = Field(default=None, exclude=True)
    homepage: str | None = Field(default=None, exclude=True)

    def to_color_system(self) -> ColorSystem:
        """Convert this theme to a ColorSystem."""
        return ColorSystem(
            **self.model_dump(
                exclude={
                    "text_area",
                    "syntax",
                    "variable",
                    "url",
                    "method",
                }
            )
        )

    def to_text_area_theme(self) -> TextAreaTheme:
        """Retrieve the TextAreaTheme corresponding to this theme."""
        if isinstance(self.syntax, SyntaxTheme):
            syntax = self.syntax.to_text_area_syntax_styles(self)
        else:
            syntax = TextAreaTheme.get_builtin_theme(self.syntax)

        text_area = self.text_area
        return TextAreaTheme(
            name=uuid.uuid4().hex,
            syntax_styles=syntax,
            gutter_style=Style.parse(text_area.gutter) if text_area.gutter else None,
            cursor_style=Style.parse(text_area.cursor) if text_area.cursor else None,
            cursor_line_style=Style.parse(text_area.cursor_line)
            if text_area.cursor_line
            else None,
            cursor_line_gutter_style=Style.parse(text_area.cursor_line_gutter)
            if text_area.cursor_line_gutter
            else None,
            bracket_matching_style=Style.parse(text_area.matched_bracket)
            if text_area.matched_bracket
            else None,
            selection_style=Style.parse(text_area.selection)
            if text_area.selection
            else None,
        )

    def to_textual_theme(self) -> TextualTheme:
        """Convert this theme to a Textual Theme.

        Returns:
            A Textual Theme instance with all properties and variables set.
        """
        theme_data = {
            "name": self.name,
            "primary": self.primary,
            "secondary": self.secondary,
            "background": self.background,
            "surface": self.surface,
            "panel": self.panel,
            "warning": self.warning,
            "error": self.error,
            "success": self.success,
            "accent": self.accent,
            "dark": self.dark,
        }

        variables = {}
        if self.url:
            url_styles = self.url.fill_with_defaults(self)
            variables.update(
                {
                    "url-base": url_styles.base,
                    "url-protocol": url_styles.protocol,
                    "url-separator": url_styles.separator,
                }
            )

        if self.variable:
            var_styles = self.variable.fill_with_defaults(self)
            variables.update(
                {
                    "variable-resolved": var_styles.resolved,
                    "variable-unresolved": var_styles.unresolved,
                }
            )

        if self.method:
            variables.update(
                {
                    "method-get": self.method.get,
                    "method-post": self.method.post,
                    "method-put": self.method.put,
                    "method-delete": self.method.delete,
                    "method-patch": self.method.patch,
                    "method-options": self.method.options,
                    "method-head": self.method.head,
                }
            )

        if self.text_area:
            if self.text_area.gutter:
                variables["text-area-gutter"] = self.text_area.gutter
            if self.text_area.cursor:
                variables["text-area-cursor"] = self.text_area.cursor
            if self.text_area.cursor_line:
                variables["text-area-cursor-line"] = self.text_area.cursor_line
            if self.text_area.cursor_line_gutter:
                variables["text-area-cursor-line-gutter"] = (
                    self.text_area.cursor_line_gutter
                )
            if self.text_area.matched_bracket:
                variables["text-area-matched-bracket"] = self.text_area.matched_bracket
            if self.text_area.selection:
                variables["text-area-selection"] = self.text_area.selection

        if isinstance(self.syntax, SyntaxTheme):
            if self.syntax.json_key:
                variables["syntax-json-key"] = self.syntax.json_key
            if self.syntax.json_string:
                variables["syntax-json-string"] = self.syntax.json_string
            if self.syntax.json_number:
                variables["syntax-json-number"] = self.syntax.json_number
            if self.syntax.json_boolean:
                variables["syntax-json-boolean"] = self.syntax.json_boolean
            if self.syntax.json_null:
                variables["syntax-json-null"] = self.syntax.json_null
        elif isinstance(self.syntax, str):
            variables["syntax-theme"] = self.syntax
        else:
            variables["syntax-theme"] = "css"

        theme_data = {k: v for k, v in theme_data.items() if v is not None}
        theme_data["variables"] = {k: v for k, v in variables.items() if v is not None}

        return TextualTheme(**theme_data)

    @staticmethod
    def text_area_theme_from_theme_variables(
        theme_variables: dict[str, str],
    ) -> TextAreaTheme:
        """Create a TextArea theme from a dictionary of theme variables.

        Args:
            theme_variables: A dictionary of theme variables.

        Returns:
            A TextAreaTheme instance configured based on the Textual theme's colors and variables.
        """
        variables = theme_variables or {}

        # Infer reasonable default syntax styles from the theme variables.
        syntax_styles = {
            "string": Style.parse(
                variables.get("syntax-json-string", variables["text-accent"])
            ),
            "number": Style.parse(
                variables.get("syntax-json-number", variables["text-secondary"])
            ),
            "boolean": Style.parse(
                variables.get("syntax-json-boolean", variables["text-success"])
            ),
            "json.null": Style.parse(
                variables.get("syntax-json-null", variables["text-warning"])
            ),
            "json.label": Style.parse(
                variables.get("syntax-json-key", variables["text-primary"])
            ),
        }

        return TextAreaTheme(
            name=uuid.uuid4().hex,
            syntax_styles=syntax_styles,
            gutter_style=Style.parse(variables.get("text-area-gutter"))
            if "text-area-gutter" in variables
            else None,
            cursor_style=Style.parse(variables.get("text-area-cursor"))
            if "text-area-cursor" in variables
            else None,
            cursor_line_style=Style.parse(variables.get("text-area-cursor-line"))
            if "text-area-cursor-line" in variables
            else None,
            cursor_line_gutter_style=Style.parse(
                variables.get("text-area-cursor-line-gutter")
            )
            if "text-area-cursor-line-gutter" in variables
            else None,
            bracket_matching_style=Style.parse(
                variables.get("text-area-matched-bracket")
            )
            if "text-area-matched-bracket" in variables
            else None,
            selection_style=Style.parse(variables.get("text-area-selection"))
            if "text-area-selection" in variables
            else None,
        )


def load_user_themes() -> dict[str, TextualTheme]:
    """Load user themes from "~/.config/posting/themes".

    Returns:
        A dictionary mapping theme names to theme objects.
    """
    directory = SETTINGS.get().theme_directory
    themes: dict[str, TextualTheme] = {}
    for path in directory.iterdir():
        path_suffix = path.suffix
        if path_suffix == ".yaml" or path_suffix == ".yml":
            with path.open() as theme_file:
                theme_content = yaml.load(theme_file, Loader=yaml.FullLoader) or {}
                try:
                    themes[theme_content["name"]] = Theme(
                        **theme_content
                    ).to_textual_theme()
                except KeyError:
                    raise ValueError(
                        f"Invalid theme file {path}. A `name` is required."
                    )
    return themes


galaxy_primary = Color.parse("#8A2BE2")
galaxy_secondary = Color.parse("#a684e8")
galaxy_warning = Color.parse("#FFD700")
galaxy_error = Color.parse("#FF4500")
galaxy_success = Color.parse("#00FA9A")
galaxy_accent = Color.parse("#FF69B4")
galaxy_background = Color.parse("#0F0F1F")
galaxy_surface = Color.parse("#1E1E3F")
galaxy_panel = Color.parse("#2D2B55")
galaxy_contrast_text = galaxy_background.get_contrast_text(1.0)

BUILTIN_THEMES: dict[str, TextualTheme] = {
    "galaxy": TextualTheme(
        name="galaxy",
        primary=galaxy_primary.hex,
        secondary=galaxy_secondary.hex,
        warning=galaxy_warning.hex,
        error=galaxy_error.hex,
        success=galaxy_success.hex,
        accent=galaxy_accent.hex,
        background=galaxy_background.hex,
        surface=galaxy_surface.hex,
        panel=galaxy_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": galaxy_primary.hex,
            "footer-background": "transparent",
        },
    ),
    "nautilus": TextualTheme(
        name="nautilus",
        primary="#0077BE",
        secondary="#20B2AA",
        warning="#FFD700",
        error="#FF6347",
        success="#32CD32",
        accent="#FF8C00",
        background="#001F3F",
        surface="#003366",
        panel="#005A8C",
        dark=True,
    ),
    "nebula": TextualTheme(
        name="nebula",
        primary="#4169E1",
        secondary="#9400D3",
        warning="#FFD700",
        error="#FF1493",
        success="#00FF7F",
        accent="#FF00FF",
        background="#0A0A23",
        surface="#1C1C3C",
        panel="#2E2E5E",
        dark=True,
    ),
    "cobalt": TextualTheme(
        name="cobalt",
        primary="#334D5C",
        secondary="#4878A6",
        warning="#FFAA22",
        error="#E63946",
        success="#4CAF50",
        accent="#D94E64",
        surface="#27343B",
        panel="#2D3E46",
        background="#1F262A",
        dark=True,
    ),
    "twilight": TextualTheme(
        name="twilight",
        primary="#367588",
        secondary="#5F9EA0",
        warning="#FFD700",
        error="#FF6347",
        success="#00FA9A",
        accent="#FF7F50",
        background="#191970",
        surface="#3B3B6D",
        panel="#4C516D",
        dark=True,
    ),
    "hacker": TextualTheme(
        name="hacker",
        primary="#00FF00",
        secondary="#3A9F3A",
        warning="#00FF66",
        error="#FF0000",
        success="#00DD00",
        accent="#00FF33",
        background="#000000",
        surface="#0A0A0A",
        panel="#111111",
        dark=True,
        variables={
            "method-get": "#00FF00",
            "method-post": "#00DD00",
            "method-put": "#00BB00",
            "method-delete": "#FF0000",
            "method-patch": "#00FF33",
            "method-options": "#3A9F3A",
            "method-head": "#00FF66",
        },
    ),
}
