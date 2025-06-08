
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Youtube, Globe, Mic, Zap, Users, Play, Download, CheckCircle, Github, ArrowRight } from "lucide-react";
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from "@/components/ui/carousel";
import { useState } from "react";
import YouTubePopup from "@/components/YouTubePopup";

const Index = () => {
  const [showYouTubePopup, setShowYouTubePopup] = useState(false);

  const features = [{
    icon: Globe,
    title: "Real-time Translation",
    description: "Instantly translate YouTube videos from any language to your preferred language with AI-powered accuracy."
  }, {
    icon: Mic,
    title: "Multiple Voice Options",
    description: "Choose from various natural-sounding voices to match your listening preference and enhance comprehension."
  }, {
    icon: Zap,
    title: "Perfect Video Sync",
    description: "Audio translation stays perfectly synchronized with the original video timing for seamless viewing."
  }, {
    icon: Users,
    title: "Universal Accessibility",
    description: "Break language barriers and make any YouTube content accessible to global audiences instantly."
  }];

  const stats = [{
    number: "5+",
    label: "Languages Supported"
  }, {
    number: "5+",
    label: "Voice Options"
  }, {
    number: "Real-time",
    label: "Translation Speed"
  }, {
    number: "Perfect",
    label: "Sync Accuracy"
  }];

  const translationSteps = [
    {
      step: "1",
      title: "Audio Extraction",
      description: "Extract audio transcript from YouTube video in real-time",
      icon: "🎵"
    },
    {
      step: "2", 
      title: "Smart Chunking",
      description: "Break down transcript into optimized chunks for processing",
      icon: "✂️"
    },
    {
      step: "3",
      title: "Murf AI Translation",
      description: "Translate each chunk using Murf AI's powerful translate API",
      icon: "🔄"
    },
    {
      step: "4",
      title: "Voice Synthesis",
      description: "Generate natural-sounding audio in target language",
      icon: "🎤"
    }
  ];

  const prototypeImages = [
    {
      title: "Extension Interface",
      description: "Clean and intuitive browser extension UI",
      src: "/one.png"
    },
    {
      title: "Language Selection",
      description: "Easy language and voice selection panel",
      src: "/two.png"
    },
    {
      title: "Real-time Translation",
      description: "Live translation overlay on YouTube videos",
      src: "/three.png"
    },
    {
      title: "Settings Panel", 
      description: "Customizable translation preferences",
      src: "/four.png"
    }
  ];

  return <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-red-500/10 to-purple-600/10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center">
            <Badge className="mb-4 bg-red-600 hover:bg-red-700 text-white border-none">
              🏆 Murf AI Hackathon Submission
            </Badge>
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 bg-gradient-to-r from-red-400 to-purple-400 bg-clip-text text-transparent">
              VoiceSync YouTube
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-4 max-w-3xl mx-auto">
              Transform any YouTube video into your language with real-time AI translation, 
              natural voice synthesis, and perfect synchronization.
            </p>
            <div className="flex items-center justify-center mb-8">
              <span className="text-gray-400 mr-2">Powered by</span>
              <span className="text-red-400 font-semibold">Murf AI Translate API</span>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Button onClick={() => window.open('https://github.com/harsh3dev/aidub', '_blank')} size="lg" className="bg-red-600 hover:bg-red-700 text-white px-8 py-4 text-lg">
                <Download className="mr-2 h-5 w-5" />
                Install Extension
              </Button>
              <Button 
                variant="outline" 
                size="lg" 
                className="border-purple-400 text-purple-400 hover:bg-purple-400 hover:text-white px-8 py-4 text-lg"
                onClick={() => setShowYouTubePopup(true)}
              >
                <Play className="mr-2 h-5 w-5" />
                Watch Demo
              </Button>
            </div>
            
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-2xl mx-auto">
              {stats.map((stat, index) => <div key={index} className="text-center">
                  <div className="text-2xl md:text-3xl font-bold text-white mb-2">{stat.number}</div>
                  <div className="text-gray-400 text-sm">{stat.label}</div>
                </div>)}
            </div>
          </div>
        </div>
      </div>

      {/* Translation Flow Section */}
      <div className="py-20 bg-black/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">How Our Translation Works</h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Powered by Murf AI's advanced translation technology for seamless multilingual experiences
            </p>
          </div>
          
          <div className="grid md:grid-cols-4 gap-8">
            {translationSteps.map((step, index) => (
              <div key={index} className="relative">
                <Card className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-all duration-300 hover:scale-105 h-full">
                  <CardHeader className="text-center pb-4">
                    <div className="text-4xl mb-4">{step.icon}</div>
                    <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-white font-bold text-sm">{step.step}</span>
                    </div>
                    <CardTitle className="text-white text-lg">{step.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-gray-300 text-center text-sm">
                      {step.description}
                    </CardDescription>
                  </CardContent>
                </Card>
                {index < translationSteps.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                    <ArrowRight className="h-6 w-6 text-purple-400" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Prototype Carousel Section */}
      <div className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Extension Preview</h2>
            <p className="text-xl text-gray-300">See our prototype in action</p>
          </div>
          
          <div className="max-w-4xl mx-auto">
            <Carousel className="w-full">
              <CarouselContent>
                {prototypeImages.map((image, index) => (
                  <CarouselItem key={index} className="basis-1/2">
                    <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
                      <div className="aspect-video bg-gradient-to-br from-red-500/20 to-purple-600/20 relative">
                        <img 
                          src={image.src} 
                          alt={image.title}
                          className="w-full h-full object-contain"
                          onError={(e) => {
                            const target = e.currentTarget as HTMLImageElement;
                            const fallback = target.nextElementSibling as HTMLElement;
                            target.style.display = 'none';
                            if (fallback) {
                              fallback.style.display = 'flex';
                            }
                          }}
                        />
                        <div className="absolute inset-0 flex items-center justify-center bg-slate-700/50" style={{display: 'none'}}>
                          <div className="text-center text-white">
                            <Youtube className="h-12 w-12 mx-auto mb-2" />
                            <p className="text-sm">{image.title}</p>
                          </div>
                        </div>
                      </div>
                      <CardHeader>
                        <CardTitle className="text-white text-lg">{image.title}</CardTitle>
                        <CardDescription className="text-gray-300">
                          {image.description}
                        </CardDescription>
                      </CardHeader>
                    </Card>
                  </CarouselItem>
                ))}
              </CarouselContent>
              <CarouselPrevious className="text-white border-slate-600 hover:bg-slate-700" />
              <CarouselNext className="text-white border-slate-600 hover:bg-slate-700" />
            </Carousel>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20 bg-black/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Powerful Features</h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Built with cutting-edge AI technology to deliver seamless translation experiences
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => <Card key={index} className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-all duration-300 hover:scale-105">
                <CardHeader className="text-center">
                  <div className="mx-auto w-12 h-12 bg-gradient-to-r from-red-500 to-purple-600 rounded-lg flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-white">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-300 text-center">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>)}
          </div>
        </div>
      </div>

      {/* Technology Stack */}
      <div className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Built with Cutting-Edge AI</h2>
            <p className="text-xl text-gray-300">Powered by advanced technologies for superior performance</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <CheckCircle className="h-6 w-6 text-green-500 mt-1" />
                <div>
                  <h3 className="text-lg font-semibold text-white">Murf AI Translate API</h3>
                  <p className="text-gray-300">Industry-leading translation with context awareness</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <CheckCircle className="h-6 w-6 text-green-500 mt-1" />
                <div>
                  <h3 className="text-lg font-semibold text-white">Advanced Speech Recognition</h3>
                  <p className="text-gray-300">Real-time audio processing with high accuracy</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <CheckCircle className="h-6 w-6 text-green-500 mt-1" />
                <div>
                  <h3 className="text-lg font-semibold text-white">Voice Synthesis Technology</h3>
                  <p className="text-gray-300">Natural-sounding voices with emotional intelligence</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <CheckCircle className="h-6 w-6 text-green-500 mt-1" />
                <div>
                  <h3 className="text-lg font-semibold text-white">Perfect Synchronization</h3>
                  <p className="text-gray-300">Frame-perfect timing alignment with video content</p>
                </div>
              </div>
            </div>
            
            <div className="relative">
              <div className="aspect-video bg-gradient-to-br from-red-500/20 to-purple-600/20 rounded-lg border border-slate-700 flex items-center justify-center">
                <div className="text-center">
                  <Youtube className="h-24 w-24 text-red-500 mx-auto mb-4" />
                  <p className="text-white text-lg">Live Demo Preview</p>
                  <p className="text-gray-400">Extension in action</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20 bg-black/20">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-white mb-6">Ready to Break Language Barriers?</h2>
          <p className="text-xl text-gray-300 mb-8">
            Join thousands of users experiencing YouTube content in their native language
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button onClick={() => window.open('https://github.com/harsh3dev/aidub', '_blank')}  size="lg" className="bg-red-600 hover:bg-red-700 text-white px-8 py-4 text-lg">
              <Download className="mr-2 h-5 w-5" />
              Download Free Extension
            </Button>
            <Button 
              variant="outline" 
              size="lg" 
              className="border-purple-400 text-purple-400 hover:bg-purple-400 hover:text-white px-8 py-4 text-lg"
              onClick={() => window.open('https://github.com/harsh3dev/aidub', '_blank')}
            >
              <Github className="mr-2 h-5 w-5" />
              View on GitHub
            </Button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-12 bg-black/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-4">VoiceSync YouTube</h3>
            <p className="text-gray-400 mb-6">
              Submitted for Murf AI Hackathon 2025 • Built with ❤️ for global accessibility
            </p>
            <div className="flex justify-center space-x-6">
              <Badge variant="outline" className="border-red-500 text-red-400">
                Real-time Translation
              </Badge>
              <Badge variant="outline" className="border-purple-500 text-purple-400">
                Murf AI Powered
              </Badge>
              <Badge variant="outline" className="border-green-500 text-green-400">
                Perfect Sync
              </Badge>
            </div>
          </div>
        </div>
      </footer>

      <YouTubePopup 
        isOpen={showYouTubePopup} 
        onClose={() => setShowYouTubePopup(false)}
        videoId="uLVY2XzrocI"
      />
    </div>;
};

export default Index;
