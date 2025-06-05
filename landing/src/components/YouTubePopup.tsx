
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface YouTubePopupProps {
  isOpen: boolean;
  onClose: () => void;
  videoId: string;
}

const YouTubePopup = ({ isOpen, onClose, videoId }: YouTubePopupProps) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl w-full bg-slate-900 border-slate-700">
        <DialogHeader className="flex flex-row items-center justify-between">
          <DialogTitle className="text-white">VoiceSync YouTube Demo</DialogTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X className="h-4 w-4" />
          </Button>
        </DialogHeader>
        <div className="aspect-video w-full">
          <iframe
            src={`https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`}
            title="VoiceSync YouTube Demo"
            className="w-full h-full rounded-lg"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default YouTubePopup;
