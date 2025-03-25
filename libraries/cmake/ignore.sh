function ignore() {
    local path="$1"
    local ignorefile="$2"

    if [ ! -f "$ignorefile" ]; then
        echo "Error: Ignore file '$ignorefile' not found." >&2
        return 1
    fi

    if grep -qFx "$path" "$ignorefile"; then
        echo "Path '$path' is ignored."
        return 0
    fi

    local parentdir="$path"
    while [ "$parentdir" != "/" ]; do
        parentdir="$(dirname "$parentdir")"
        if grep -qFx "$parentdir" "$ignorefile"; then
            echo "Path '$path' is ignored because its parent '$parentdir' is ignored."
            return 0
        fi
    done

    echo "Path '$path' is not ignored."
    return 1
}

