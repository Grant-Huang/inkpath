#!/bin/bash
# Restore @/ aliases for all imports

cd /Users/admin/Desktop/work/inkpath/frontend

# app/
sed -i '' 's|../components/|@/components/|g' app/*.tsx
sed -i '' 's|../../components/|@/components/|g' app/**/*.tsx

# components/
sed -i '' 's|../lib/|@/lib/|g' components/**/*.tsx
sed -i '' 's|../../lib/|@/lib/|g' components/**/*.tsx
sed -i '' 's|../hooks/|@/hooks/|g' components/**/*.tsx
sed -i '' 's|../../hooks/|@/hooks/|g' components/**/*.tsx
sed -i '' 's|../stories/|@/components/stories/|g' components/**/*.tsx

# hooks/
sed -i '' 's|../lib/|@/lib/|g' hooks/*.ts

echo "Done restoring @/ aliases"
