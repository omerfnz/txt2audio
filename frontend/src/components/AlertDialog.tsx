import { AlertTriangle, X } from 'lucide-react';
import { clsx } from 'clsx';

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
    if (!isOpen) return null;

    const variantStyles = {
        danger: {
            icon: 'text-red-500',
            button: 'bg-red-600 hover:bg-red-500 text-white',
            border: 'border-red-500/30'
        },
        warning: {
            icon: 'text-yellow-500',
            button: 'bg-yellow-600 hover:bg-yellow-500 text-white',
            border: 'border-yellow-500/30'
        },
        info: {
            icon: 'text-blue-500',
            button: 'bg-blue-600 hover:bg-blue-500 text-white',
            border: 'border-blue-500/30'
        }
    };

    const styles = variantStyles[variant];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onCancel}
            />
            
            {/* Dialog */}
            <div className={clsx(
                "relative glass rounded-2xl border-2 p-6 max-w-md w-full mx-4 shadow-2xl animate-slide-up",
                styles.border
            )}>
                {/* Close button */}
                <button
                    onClick={onCancel}
                    className="absolute top-4 right-4 p-1 rounded-lg hover:bg-white/10 transition-colors text-slate-400 hover:text-slate-200"
                >
                    <X className="w-5 h-5" />
                </button>

                {/* Icon and Title */}
                <div className="flex items-start gap-4 mb-4">
                    <div className={clsx("p-3 rounded-xl bg-white/5", styles.icon)}>
                        <AlertTriangle className="w-6 h-6" />
                    </div>
                    <div className="flex-1">
                        <h3 className="text-lg font-bold text-slate-100 mb-1">
                            {title}
                        </h3>
                    </div>
                </div>

                {/* Message */}
                <p className="text-slate-300 mb-6 ml-16">
                    {message}
                </p>

                {/* Actions */}
                <div className="flex gap-3 justify-end">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors font-medium"
                    >
                        {cancelText}
                    </button>
                    <button
                        onClick={onConfirm}
                        className={clsx(
                            "px-4 py-2 rounded-lg transition-colors font-medium",
                            styles.button
                        )}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
}

