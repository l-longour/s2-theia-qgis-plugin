# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import sys, os
import subprocess
from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtWidgets import QDateTimeEdit, QDateEdit
from qgis.PyQt.QtCore import QCoreApplication, QDate
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFolderDestination)
from qgis import processing

def tr(string):
    return QCoreApplication.translate('Processing', string)

class DateWidget(WidgetWrapper):
    """
    QDateTimeEdit widget with calendar pop up
    """

    def createWidget(self):
        self._combo = QDateEdit()
        self._combo.setCalendarPopup(True)

        today = QDate.currentDate()
        self._combo.setDate(today)

        return self._combo

    def value(self):
        date_chosen = self._combo.dateTime()
        return date_chosen.toString(Qt.ISODate)

class DownloadSentinel2Algorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    IN_EXTENT = 'EXTENT'
    IN_LEVEL = 'LEVEL'
    IN_ID = 'ID'
    IN_PW = 'PW'
    IN_SAVE_PW = 'SAVE_PW'
    IN_DATE_MIN = 'DATE_MIN'
    IN_DATE_MAX = 'DATE_MAX'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DownloadSentinel2Algorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'myscript'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Télécharger des données Sentinel-2')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Example scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'examplescripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Télécharger des données Sentinel-2 depuis le centre de production MUSCATE de THEIA.")
    
    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        #self.addParameter(
        #    QgsProcessingParameterFeatureSource(
        #        self.INPUT,
        #        self.tr('Input'),
        #        [QgsProcessing.TypeVectorAnyGeometry]
        #    )
        #)
        
        #self.addParameter(
        #    QgsProcessingParameterString(
        #        self.IN_DATE_MIN,
        #        self.tr('Date minimale'))
        #    )
            
        #self.addParameter(
        #    QgsProcessingParameterString(
        #        self.IN_DATE_MAX,
        #        self.tr('Date maximale'))
        #    )
        
        datDeb = QgsProcessingParameterString(self.IN_DATE_MIN, 'Date minimale')
        datDeb.setMetadata({
            'widget_wrapper': {
                'class': DateWidget}})

        self.addParameter(datDeb)
        
        datFin = QgsProcessingParameterString(self.IN_DATE_MAX, 'Date maximale')
        datFin.setMetadata({
            'widget_wrapper': {
                'class': DateWidget}})

        self.addParameter(datFin)
        
        self.addParameter(
            QgsProcessingParameterExtent(
                self.IN_EXTENT,
                'Emprise du projet', 
                defaultValue=None))
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_LEVEL,
                tr('Niveau de traitement'),
                options=[tr('LEVEL2A'), tr('LEVEL3A')],
                defaultValue=0,
                optional=False)
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT,
                self.tr('Images S2')
            )
        )
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        
        #self.addParameter(
        #    QgsProcessingParameterFeatureSink(
        #        self.OUTPUT,
        #        self.tr('Output layer')
        #    )
        #)
        
        params = []
        params.append(QgsProcessingParameterString(self.IN_ID,
                                                   self.tr('Utilisateur'),
                                                   optional=False))
        params.append(QgsProcessingParameterString(self.IN_PW,
                                                   self.tr('Mot de passe'),
                                                   optional=False))
                                                   
                                                   
        params.append(QgsProcessingParameterBoolean(self.IN_SAVE_PW,
                                                    description="garder en mémoire",
                                                    optional=True,
                                                    defaultValue=False))
                                                   
        for p in params:
            p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
            self.addParameter(p)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        
        mydate = self.parameterAsString(
            parameters,
            self.INIDATE,
            context
        )

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs()
        )

        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(source.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Add a feature in the sink
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        # To run another Processing algorithm as part of this algorithm, you can use
        # processing.run(...). Make sure you pass the current context and feedback
        # to processing.run to ensure that all temporary layer outputs are available
        # to the executed algorithm, and that the executed algorithm can send feedback
        # reports to the user (and correctly handle cancellation and progress reports!)
        if False:
            buffered_layer = processing.run("native:buffer", {
                'INPUT': dest_id,
                'DISTANCE': 1.5,
                'SEGMENTS': 5,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'DISSOLVE': False,
                'OUTPUT': 'memory:'
            }, context=context, feedback=feedback)['OUTPUT']

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: dest_id}
