import * as React from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface PaginationProps extends React.HTMLAttributes<HTMLDivElement> {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  siblingCount?: number
}

const Pagination = React.forwardRef<HTMLDivElement, PaginationProps>(
  ({ className, currentPage, totalPages, onPageChange, siblingCount = 1, ...props }, ref) => {
    if (totalPages <= 0) return null

    const siblings = React.useMemo(() => {
      const pages: (number | "...")[] = []
      const leftSiblingIndex = Math.max(currentPage - siblingCount, 1)
      const rightSiblingIndex = Math.min(currentPage + siblingCount, totalPages)

      const showLeftDots = leftSiblingIndex > 2
      const showRightDots = rightSiblingIndex < totalPages - 1

      if (!showLeftDots && !showRightDots) {
        for (let i = 1; i <= Math.min(3, totalPages); i++) {
          pages.push(i)
        }
        if (totalPages > 3) {
          pages.push("...")
          pages.push(totalPages)
        }
      } else if (showLeftDots && !showRightDots) {
        pages.push(1)
        pages.push("...")
        for (let i = Math.max(totalPages - 2, 2); i <= totalPages; i++) {
          pages.push(i)
        }
      } else if (!showLeftDots && showRightDots) {
        for (let i = 1; i <= Math.min(3, totalPages); i++) {
          pages.push(i)
        }
        pages.push("...")
        pages.push(totalPages)
      } else {
        pages.push(1)
        if (leftSiblingIndex > 2) pages.push("...")
        for (let i = leftSiblingIndex; i <= rightSiblingIndex; i++) {
          pages.push(i)
        }
        if (rightSiblingIndex < totalPages - 1) pages.push("...")
        pages.push(totalPages)
      }

      return pages
    }, [currentPage, totalPages, siblingCount])

    return (
      <nav
        ref={ref}
        className={cn("flex items-center justify-center gap-1", className)}
        aria-label="pagination"
        {...props}
      >
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
        >
          Previous
        </Button>

        <div className="flex items-center gap-1">
          {siblings.map((page, index) =>
            page === "..." ? (
              <span
                key={`dots-${index}`}
                className="flex h-9 w-9 items-center justify-center"
              >
                ...
              </span>
            ) : (
              <Button
                key={page}
                variant={currentPage === page ? "default" : "outline"}
                size="sm"
                onClick={() => onPageChange(page)}
              >
                {page}
              </Button>
            )
          )}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          Next
        </Button>
      </nav>
    )
  }
)
Pagination.displayName = "Pagination"

export { Pagination }
