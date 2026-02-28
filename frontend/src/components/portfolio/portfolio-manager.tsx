"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Plus,
  Briefcase,
  Trash2,
  ChevronDown,
  ChevronUp,
  X,
  Loader2,
  Search,
  AlertCircle,
  FolderOpen,
} from "lucide-react";
import { toast } from "sonner";
import {
  getPortfolios,
  createPortfolio,
  deletePortfolio,
  addStockToPortfolio,
  removeStockFromPortfolio,
  getPortfolioAlpha,
} from "@/lib/api";
import { StockSearch } from "@/components/stocks/stock-search";
import type { Portfolio } from "@/types/api";
import type { Stock } from "@/types/stock";

export function PortfolioManager() {
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [addStockOpen, setAddStockOpen] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [activePortfolioId, setActivePortfolioId] = useState<string | null>(
    null
  );
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");

  // Fetch portfolios
  const {
    data: portfoliosData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["portfolios"],
    queryFn: getPortfolios,
  });

  const portfolios = portfoliosData?.portfolios ?? [];

  // Create portfolio mutation
  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      createPortfolio(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      setCreateOpen(false);
      setNewName("");
      setNewDescription("");
      toast.success("Portfolio created successfully");
    },
    onError: (err) => {
      toast.error(
        `Failed to create portfolio: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    },
  });

  // Delete portfolio mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePortfolio(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      setDeleteConfirmId(null);
      toast.success("Portfolio deleted");
    },
    onError: (err) => {
      toast.error(
        `Failed to delete portfolio: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    },
  });

  // Add stock mutation
  const addStockMutation = useMutation({
    mutationFn: ({
      portfolioId,
      ticker,
    }: {
      portfolioId: string;
      ticker: string;
    }) => addStockToPortfolio(portfolioId, ticker),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      setAddStockOpen(false);
      toast.success("Stock added to portfolio");
    },
    onError: (err) => {
      toast.error(
        `Failed to add stock: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    },
  });

  // Remove stock mutation
  const removeStockMutation = useMutation({
    mutationFn: ({
      portfolioId,
      ticker,
    }: {
      portfolioId: string;
      ticker: string;
    }) => removeStockFromPortfolio(portfolioId, ticker),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      toast.success("Stock removed from portfolio");
    },
    onError: (err) => {
      toast.error(
        `Failed to remove stock: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    },
  });

  const handleCreatePortfolio = () => {
    if (!newName.trim()) return;
    createMutation.mutate({
      name: newName.trim(),
      description: newDescription.trim() || undefined,
    });
  };

  const handleAddStock = (stock: Stock) => {
    if (!activePortfolioId) return;
    addStockMutation.mutate({
      portfolioId: activePortfolioId,
      ticker: stock.ticker,
    });
  };

  const handleRemoveStock = (portfolioId: string, ticker: string) => {
    removeStockMutation.mutate({ portfolioId, ticker });
  };

  const openAddStockDialog = (portfolioId: string) => {
    setActivePortfolioId(portfolioId);
    setAddStockOpen(true);
  };

  if (error) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-8 text-center">
          <AlertCircle className="mb-2 h-8 w-8 text-destructive" />
          <p className="text-sm text-destructive">Failed to load portfolios</p>
          <p className="text-xs text-muted-foreground mt-1">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Briefcase className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold">Portfolios</h2>
        </div>

        {/* Create Portfolio Dialog */}
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-1.5">
              <Plus className="h-4 w-4" />
              New Portfolio
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Portfolio</DialogTitle>
              <DialogDescription>
                Create a new portfolio to track a group of stocks
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="portfolio-name">
                  Name
                </label>
                <Input
                  id="portfolio-name"
                  placeholder="e.g., Tech Watchlist"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) =>
                    e.key === "Enter" && handleCreatePortfolio()
                  }
                />
              </div>
              <div className="space-y-2">
                <label
                  className="text-sm font-medium"
                  htmlFor="portfolio-description"
                >
                  Description (optional)
                </label>
                <Input
                  id="portfolio-description"
                  placeholder="Brief description..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setCreateOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreatePortfolio}
                disabled={!newName.trim() || createMutation.isPending}
              >
                {createMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-5 w-32" />
                  <Skeleton className="h-5 w-16 rounded-full" />
                </div>
                <Skeleton className="h-4 w-48 mt-1" />
              </CardHeader>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && portfolios.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <FolderOpen className="mb-3 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm font-medium text-muted-foreground">
              No portfolios yet
            </p>
            <p className="text-xs text-muted-foreground/70 mt-1 mb-4">
              Create your first portfolio to start tracking stocks
            </p>
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5"
              onClick={() => setCreateOpen(true)}
            >
              <Plus className="h-4 w-4" />
              Create Portfolio
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Portfolio List */}
      {portfolios.map((portfolio) => (
        <PortfolioCard
          key={portfolio.id}
          portfolio={portfolio}
          isExpanded={expandedId === portfolio.id}
          onToggleExpand={() =>
            setExpandedId(expandedId === portfolio.id ? null : portfolio.id)
          }
          onAddStock={() => openAddStockDialog(portfolio.id)}
          onRemoveStock={(ticker) =>
            handleRemoveStock(portfolio.id, ticker)
          }
          onDelete={() => setDeleteConfirmId(portfolio.id)}
          isRemovingStock={removeStockMutation.isPending}
        />
      ))}

      {/* Add Stock Dialog */}
      <Dialog open={addStockOpen} onOpenChange={setAddStockOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add Stock to Portfolio</DialogTitle>
            <DialogDescription>
              Search for a stock to add to your portfolio
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <StockSearch onSelect={handleAddStock} compact />
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmId !== null}
        onOpenChange={(open) => !open && setDeleteConfirmId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Portfolio</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this portfolio? This action cannot
              be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteConfirmId(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() =>
                deleteConfirmId && deleteMutation.mutate(deleteConfirmId)
              }
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ─── Portfolio Card Sub-component ──────────────────────────────────────────

interface PortfolioCardProps {
  portfolio: Portfolio;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onAddStock: () => void;
  onRemoveStock: (ticker: string) => void;
  onDelete: () => void;
  isRemovingStock: boolean;
}

function PortfolioCard({
  portfolio,
  isExpanded,
  onToggleExpand,
  onAddStock,
  onRemoveStock,
  onDelete,
  isRemovingStock,
}: PortfolioCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <button
              type="button"
              onClick={onToggleExpand}
              className="flex items-center gap-2 text-left flex-1 min-w-0"
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
              )}
              <div className="min-w-0">
                <CardTitle className="text-base truncate">
                  {portfolio.name}
                </CardTitle>
                {portfolio.description && (
                  <CardDescription className="truncate">
                    {portfolio.description}
                  </CardDescription>
                )}
              </div>
            </button>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Badge variant="secondary" className="text-xs">
              {portfolio.stocks.length} stock
              {portfolio.stocks.length !== 1 ? "s" : ""}
            </Badge>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-destructive hover:text-destructive"
              onClick={onDelete}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Mini stock ticker list when collapsed */}
        {!isExpanded && portfolio.stocks.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {portfolio.stocks.slice(0, 8).map((s) => (
              <Badge key={s.ticker} variant="outline" className="text-xs">
                {s.ticker}
              </Badge>
            ))}
            {portfolio.stocks.length > 8 && (
              <Badge variant="outline" className="text-xs">
                +{portfolio.stocks.length - 8} more
              </Badge>
            )}
          </div>
        )}
      </CardHeader>

      {/* Expanded Content */}
      {isExpanded && (
        <CardContent className="pt-0">
          <Separator className="mb-3" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-muted-foreground">
              Stocks in portfolio
            </span>
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5 h-7 text-xs"
              onClick={onAddStock}
            >
              <Plus className="h-3 w-3" />
              Add Stock
            </Button>
          </div>

          {portfolio.stocks.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-6 text-center">
              <Search className="mb-2 h-6 w-6 text-muted-foreground/50" />
              <p className="text-xs text-muted-foreground">
                No stocks in this portfolio
              </p>
              <Button
                size="sm"
                variant="link"
                className="mt-1 h-auto p-0 text-xs"
                onClick={onAddStock}
              >
                Add your first stock
              </Button>
            </div>
          ) : (
            <ScrollArea className="max-h-[300px]">
              <div className="space-y-1">
                {portfolio.stocks.map((stock, index) => (
                  <div key={stock.ticker}>
                    <div className="flex items-center justify-between rounded-lg p-2.5 transition-colors hover:bg-muted/50">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold">{stock.ticker}</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {stock.company_name}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground hover:text-destructive shrink-0"
                        onClick={() => onRemoveStock(stock.ticker)}
                        disabled={isRemovingStock}
                      >
                        <X className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                    {index < portfolio.stocks.length - 1 && <Separator />}
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      )}
    </Card>
  );
}
