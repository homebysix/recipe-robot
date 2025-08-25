//
//  AHHelpPopover.m
//
//  Recipe Robot
//  Copyright 2015-2025 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
//

#import "AHHelpPopover.h"

static const int HELP_POPOVER_WIDTH = 400;
static const double HELP_POPOVER_TITLE_FACTOR = 1.2;

static const int HELP_POPOVER_PREFERRED_EDGE = NSMinYEdge;
static const int HELP_POPOVER_FRAME_PADDING = 20;

static NSString *const BUTTON_URL_KEY = @"URL";
static NSString *const BUTTON_TITLE_KEY = @"Title";

static NSString * AHHPLocalizedString(NSString *key, NSString *comment)
{
    return [[NSBundle mainBundle] localizedStringForKey:key
                                                  value:key
                                                  table:@"LocalizableHelpPopover"];
}

static NSString *NO_HELP_AVAILABLE() {
    /* This is a function so the string can be localized if you so choose */
    static dispatch_once_t onceToken;
    __strong static NSString *string = nil;
    dispatch_once(&onceToken,
                  ^{ string = AHHPLocalizedString(@"No help available", nil); });
    return string;
};

#pragma mark - AHHelpPopover
@interface AHHelpPopover ()<NSTextFieldDelegate>
@end

@implementation AHHelpPopover {
    BOOL _isInternallyObservingClose;
}

@synthesize helpTitle;
@synthesize helpText;
@synthesize attributedHelpText;
@synthesize helpURL;
@synthesize sender;
@synthesize helpTitleFont;
@synthesize helpTextFont;
@synthesize width;
@synthesize senderEdge;
@synthesize textAlignment;
@synthesize completionHandler;

#pragma mark - Init / Dealloc
- (void)dealloc {
    if (_isInternallyObservingClose) {
        [[NSNotificationCenter defaultCenter]
            removeObserver:self
                      name:NSPopoverDidCloseNotification
                    object:self];
    }
}

- (instancetype)init {
    if (self = [super init]) {
        width = HELP_POPOVER_WIDTH;
        senderEdge = HELP_POPOVER_PREFERRED_EDGE;
        helpTextFont = [NSFont systemFontOfSize:12];
    }
    return self;
}

- (instancetype)initWithSender:(NSView *)sender {
    if (self = [self init]) {
        sender = sender;
    }
    return self;
}

#pragma mark - Open Popopver
- (void)openPopover {
    if (!self.isShown) {

        // Always be transient.
        self.behavior = NSPopoverBehaviorTransient;

        // Main view controller for the popover.
        NSViewController *popoverViewController = [[NSViewController alloc] init];

        /* NSTextStorage is a subclass of NSAttributed string
         * that we can apply a layout manager to. */
        NSTextStorage *textStorage = [[NSTextStorage alloc] init];

        /* NSTextContainer is used to calculate the size of the popover. To begin
         * set it to the _width, and max height, which will get shortened later. */
        NSTextContainer *textContainer = [[NSTextContainer alloc] initWithContainerSize:NSMakeSize(self.width, FLT_MAX)];

        [textContainer setLineFragmentPadding:5.0];

        // Append the help text.
        [textStorage appendAttributedString:self.attributedHelpText];

        // Append the title.
        if (self.helpTitle.length) {

            /* If a title font hasn't been explicitly declaired try and match the help text
             * font. If the help text has no associated font, just use system default. */
            NSFont *currentFont = nil;
            if (!self.helpTitleFont) {

                NSInteger fontSize = (NSInteger) [NSFont systemFontSize];

                if((currentFont = [textStorage attribute:NSFontAttributeName
                                                                 atIndex:1
                                                          effectiveRange:nil])) {

                NSDictionary *attrs = currentFont.fontDescriptor.fontAttributes;

                if (attrs[NSFontSizeAttribute]) {
                    fontSize = [attrs[NSFontSizeAttribute] integerValue];
                }

                NSInteger titleSize = (NSInteger) (fontSize * HELP_POPOVER_TITLE_FACTOR);

                self.helpTitleFont = [NSFont fontWithDescriptor:currentFont.fontDescriptor
                                                  size:titleSize];

                self.helpTitleFont = [[NSFontManager sharedFontManager] convertFont:self.helpTitleFont
                                                                toHaveTrait:NSBoldFontMask];

                } else {
                    self.helpTitleFont = [NSFont boldSystemFontOfSize:fontSize * HELP_POPOVER_TITLE_FACTOR];  // suitable default.
                }
            }

            NSDictionary *attributes = @{
                                         NSFontAttributeName : self.helpTitleFont,
                                         };

            NSAttributedString *title = [[NSAttributedString alloc] initWithString:[self.helpTitle stringByAppendingString:@"\n\n"]
                                                                        attributes:attributes];

            [textStorage insertAttributedString:title atIndex:0];
        }

        // Append a link.
        if (self.helpURL) {
            NSString *helpLinkString = [@"\n\n" stringByAppendingString:self.helpURL.absoluteString];
            NSAttributedString *urlString = [[NSAttributedString alloc] initWithString:helpLinkString attributes:@{NSLinkAttributeName : self.helpURL}];

            [textStorage appendAttributedString:urlString];
        }

        /* Using layout manager we can determine the
         * required frame rect to hold the help text */
        NSLayoutManager *layoutManager = [[NSLayoutManager alloc] init];
        [layoutManager addTextContainer:textContainer];

        [textStorage addLayoutManager:layoutManager];

        /* Perform glyph generation and layout */
        [layoutManager glyphRangeForTextContainer:textContainer];

        NSRect viewFrame = [layoutManager usedRectForTextContainer:textContainer];
        viewFrame.size.height += 10;  // Pad the height by 10.

        /* We want to use NSTextView rather than the textContainer
         * created above to allow for a clickable URL link */
        NSTextView *helpTextView = [[NSTextView alloc] initWithFrame:viewFrame];
        helpTextView.editable = NO;
        helpTextView.backgroundColor = [NSColor clearColor];
        helpTextView.alignment = self.textAlignment;

        [helpTextView.textStorage setAttributedString:textStorage];

        /* Pad the viewFrame a little bit */
        viewFrame.size.width += HELP_POPOVER_FRAME_PADDING;
        viewFrame.size.height += HELP_POPOVER_FRAME_PADDING;

        /* Initialize the main view */
        NSView *view = [[NSView alloc] initWithFrame:viewFrame];

        /* Now we have our padded view, add the helpTextView as a subview */
        [view addSubview:helpTextView];

        /* Calculate the frameOrigin to center the helpTextField inside of the parent view. */
        NSPoint centerPoint = NSMakePoint(
                                (viewFrame.size.width - helpTextView.frame.size.width) / 2,
                                (viewFrame.size.height - helpTextView.frame.size.height) / 2);

        [helpTextView setFrameOrigin:centerPoint];

        [helpTextView setAutoresizingMask:NSViewMinXMargin | NSViewMaxXMargin |
                                          NSViewMinYMargin | NSViewMaxYMargin];


        popoverViewController.view = view;
        self.contentViewController = popoverViewController;

        [self startObserving];

        [self showRelativeToRect:self.sender.bounds
                          ofView:self.sender
                   preferredEdge:self.senderEdge];
    }
}

- (void)openPopoverWithCompletionHandler:(void (^)(void))complete {
    if (complete) {
        self.completionHandler = complete;
    }
    [self openPopover];
}

- (void)openPopoverFromButton:(NSButton *)sender
         witAttributeHelpText:(NSAttributedString *)helpText {
    self.sender = sender;
    self.attributedHelpText = helpText;
    [self openPopover];
}

- (void)openPopoverFromButton:(NSButton *)sender
            witHelpTextFormat:(NSString *)format, ... {
    va_list args;
    va_start(args, format);
    NSString *helpText = [[NSString alloc] initWithFormat:format
                                                arguments:args];
    va_end(args);

    self.sender = sender;
    self.helpText = helpText;
    [self openPopover];
}

# pragma mark - Accessors
- (NSAttributedString *)attributedHelpText {
    if (!self.attributedHelpText && self.helpText) {
        self.attributedHelpText = [[NSAttributedString alloc] initWithString:self.helpText
                                                              attributes:@{NSFontAttributeName : self.helpTextFont}];
    }
    return self.attributedHelpText;
}

#pragma  mark - Observing
- (void)startObserving {
    _isInternallyObservingClose = YES;
    [[NSNotificationCenter defaultCenter]
     addObserver:self
     selector:@selector(executeCompletionHandler:)
     name:NSPopoverDidCloseNotification
     object:self];
}

- (void)executeCompletionHandler:(NSNotification *)notification {
    if (self.completionHandler) {
        self.completionHandler();
        self.completionHandler = nil;
    }
}

@end

#pragma mark -
#pragma mark AHHelpPopoverButton

@implementation AHHelpPopoverButton

@synthesize helpText;
@synthesize helpTitle;
@synthesize helpLink;

- (void)awakeFromNib {
    self.target = self;
    self.action = @selector(openPopover);
}

- (void)openPopover {
    AHHelpPopover *popover = [[AHHelpPopover alloc] initWithSender:self];
    popover.helpText = self.helpText;

    if (self.helpTitle.length) {
        popover.helpTitle = self.helpTitle;
    }

    if (self.helpLink.length) {
        popover.helpURL = [NSURL URLWithString:self.helpLink];
    }

    self.enabled = NO;
    popover.completionHandler = ^() {
        self.enabled = YES;
    };

    [popover openPopover];
}

# pragma mark - Accessors
- (NSString *)helpText {
    if (!self.helpText && (self.helpText = [self localizedStringValueForIvar:self.helpText
                                              appendingIdentifierKey:nil]).length == 0) {
        /* If the help text is the same as the identifier no
         * value was found in the Localizable.strings file,
         * so set it to a "No help available" message */
        self.helpText = NO_HELP_AVAILABLE();
    }
    return self.helpText;
}

- (void)helpTextWithFormat:(NSString *)format, ... {
    va_list args;
    va_start(args, format);
    self.helpText = [[NSString alloc] initWithFormat:format
                                       arguments:args];
    va_end(args);
}

- (NSString *)helpLink {
    return (self.helpLink ?: (self.helpLink = [self localizedStringValueForIvar:self.helpLink
                                                 appendingIdentifierKey:BUTTON_URL_KEY]));
}

- (NSString *)helpTitle {
    return (self.helpTitle ?: (self.helpTitle = [self localizedStringValueForIvar:self.helpTitle
                                                   appendingIdentifierKey:BUTTON_TITLE_KEY]));
}


#pragma mark - Util
- (NSString *)localizedStringValueForIvar:(NSString *)iVar
                   appendingIdentifierKey:(NSString *)keyVal {
    if (!iVar) {
        NSString *key = [self.identifier stringByAppendingString:keyVal ?: @""];
        NSString *title = AHHPLocalizedString(key, nil);

        /* If the key is different than the results a string was
         * found in the Localized.strings so update the iVar*/
        if ([title isEqualToString:key] == NO) {
            iVar = title;
        }
    }
    return iVar;
}

@end
