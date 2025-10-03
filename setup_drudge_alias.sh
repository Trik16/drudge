#!/bin/bash
# Setup script for Drudge CLI alias

# Get the absolute path to the WorkLog directory
SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

# Detect the user's default shell from their config files
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    echo "Could not find .zshrc or .bashrc. Please add the alias manually."
    exit 1
fi

# Remove old worklog, wl aliases, and drudge functions if they exist
sed -i.bak '/alias worklog=/d; /alias wl=/d; /alias drudge=/d; /# Drudge CLI/d; /drudge()/,/^}/d; /worklog()/,/^}/d; /wl()/,/^}/d' "$SHELL_RC" 2>/dev/null

# Add new drudge function with absolute path
cat >> "$SHELL_RC" << EOF

# Drudge CLI - Work time tracking tool
drudge() {
    (cd $SCRIPT_DIR && python3 -m src.worklog "\$@")
}
worklog() {
    drudge "\$@"
}
wl() {
    drudge "\$@"
}
EOF

echo "✅ Drudge CLI alias added to $SHELL_RC"
echo ""
echo "To use immediately, run:"
echo "  source $SHELL_RC"
echo ""
echo "Usage:"
echo "  drudge start 'My Task'"
echo "  drudge status"
echo "  drudge --help"
