import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface AlertDialogProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    onConfirm: () => void;
    onCancel: () => void;
    variant?: 'danger' | 'warning' | 'info';
}

export function AlertDialog({
    isOpen,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    onConfirm,
    onCancel,
    variant = 'danger'
}: AlertDialogProps) {
    const variantStyles = {
        danger: {
            icon: 'text-destructive',
            buttonVariant: 'destructive' as const,
        },
        warning: {
            icon: 'text-yellow-500',
            buttonVariant: 'default' as const,
        },
        info: {
            icon: 'text-blue-500',
            buttonVariant: 'default' as const,
        }
    };

    const styles = variantStyles[variant];

    return (
        <Dialog open={isOpen} onOpenChange={(open: boolean) => !open && onCancel()}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <div className="flex items-start gap-4">
                        <div className={cn("p-3 rounded-xl bg-muted/50", styles.icon)}>
                            <AlertTriangle className="w-6 h-6" />
                        </div>
                        <div className="flex-1">
                            <DialogTitle className="text-left">{title}</DialogTitle>
                        </div>
                    </div>
                </DialogHeader>
                <DialogDescription className="ml-16 text-left">
                    {message}
                </DialogDescription>
                <DialogFooter className="sm:justify-end gap-2">
                    <Button
                        variant="outline"
                        onClick={onCancel}
                    >
                        {cancelText}
                    </Button>
                    <Button
                        variant={styles.buttonVariant}
                        onClick={onConfirm}
                    >
                        {confirmText}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

