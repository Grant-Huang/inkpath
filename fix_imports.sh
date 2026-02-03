#!/bin/bash
# Fix path aliases to relative paths

cd /Users/admin/Desktop/work/inkpath/frontend

# Replace @/lib/api -> ../../lib/api
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/lib/api|../../lib/api|g'
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/lib/dataMapper|../../lib/dataMapper|g'
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/lib/types|../../lib/types|g'
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/lib/polling|../../lib/polling|g'

# Replace @/hooks/* -> ../../hooks
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/hooks/|../../hooks/|g'

# Replace @/components/pages/* -> ../../components/pages
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/components/pages/|../../components/pages/|g'

# Replace @/components/stories/* -> ../../components/stories
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/components/stories/|../../components/stories/|g'

# Replace @/components/discussion/* -> ../../components/discussion
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/components/discussion/|../../components/discussion/|g'

# Replace @/components/segments/* -> ../../components/segments
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/components/segments/|../../components/segments/|g'

# Replace @/components/branches/* -> ../../components/branches
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/components/branches/|../../components/branches/|g'

# Replace @/components/common/* -> ../../components/common
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/components/common/|../../components/common/|g'

# Replace @/components/layout/* -> ../../components/layout
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs sed -i '' 's|@/components/layout/|../../components/layout/|g'

echo "Done fixing imports"
